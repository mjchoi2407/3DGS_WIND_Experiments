#!/usr/bin/env python3
"""GOF mesh extraction을 실험용 파라미터로 실행한다."""

from __future__ import annotations

import json
import os
import random
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
GOF_DIR = PROJECT_ROOT / "external" / "gaussian-opacity-fields"
if str(GOF_DIR) not in sys.path:
    sys.path.insert(0, str(GOF_DIR))

import numpy as np
import torch
import trimesh
from arguments import ModelParams, PipelineParams, get_combined_args
from gaussian_renderer import integrate
from scene import Scene
from scene.cameras import Camera
from scene.gaussian_model import GaussianModel, get_frustum_mask
from tetranerf.utils.extension import cpp
from tqdm import tqdm
from utils.general_utils import build_rotation
from utils.tetmesh import marching_tetrahedra


@torch.no_grad()
def evaluate_alpha(
    points: torch.Tensor,
    views: List[Camera],
    gaussians: GaussianModel,
    pipeline,
    background: torch.Tensor,
    kernel_size: float,
    return_color: bool = False,
):
    final_alpha = torch.ones((points.shape[0]), dtype=torch.float32, device="cuda")
    if return_color:
        final_color = torch.ones((points.shape[0], 3), dtype=torch.float32, device="cuda")

    for _, view in enumerate(tqdm(views, desc="Rendering progress")):
        ret = integrate(points, view, gaussians, pipeline, background, kernel_size=kernel_size)
        alpha_integrated = ret["alpha_integrated"]
        if return_color:
            color_integrated = ret["color_integrated"]
            final_color = torch.where(
                (alpha_integrated < final_alpha).reshape(-1, 1),
                color_integrated,
                final_color,
            )
        final_alpha = torch.min(final_alpha, alpha_integrated)

    alpha = 1 - final_alpha
    if return_color:
        return alpha, final_color
    return alpha


@torch.no_grad()
def get_tetra_points_with_multiplier(
    gaussians: GaussianModel,
    views: List[Camera],
    tetra_scale_multiplier: float,
    near: float,
    far: float,
):
    box = trimesh.creation.box()
    box.vertices *= 2

    rots = build_rotation(gaussians._rotation)
    xyz = gaussians.get_xyz
    scale = gaussians.get_scaling_with_3D_filter * tetra_scale_multiplier

    vertices = box.vertices.T
    vertices = torch.from_numpy(vertices).float().cuda().unsqueeze(0).repeat(xyz.shape[0], 1, 1)
    vertices = vertices * scale.unsqueeze(-1)
    vertices = torch.bmm(rots, vertices).squeeze(-1) + xyz.unsqueeze(-1)
    vertices = vertices.permute(0, 2, 1).reshape(-1, 3).contiguous()
    vertices = torch.cat([vertices, xyz], dim=0)

    point_scale = scale.max(dim=-1, keepdim=True)[0]
    scale_corner = point_scale.repeat(1, 8).reshape(-1, 1)
    vertices_scale = torch.cat([scale_corner, point_scale], dim=0)

    vertex_mask = get_frustum_mask(vertices, views, near, far)
    return vertices[vertex_mask], vertices_scale[vertex_mask]


@torch.no_grad()
def apply_proxy_multipliers(
    gaussians: GaussianModel,
    gaussian_scale_multiplier: float,
    filter3d_multiplier: float,
) -> None:
    if gaussian_scale_multiplier <= 0:
        raise ValueError("--gaussian-scale-multiplier는 0보다 커야 한다.")
    if filter3d_multiplier < 0:
        raise ValueError("--filter3d-multiplier는 0 이상이어야 한다.")

    if gaussian_scale_multiplier != 1.0:
        gaussians._scaling = gaussians._scaling + torch.log(
            torch.tensor(gaussian_scale_multiplier, dtype=gaussians._scaling.dtype, device="cuda")
        )
    if filter3d_multiplier != 1.0:
        gaussians.filter_3D = gaussians.filter_3D * filter3d_multiplier


@torch.no_grad()
def marching_tetrahedra_with_binary_search(
    model_path: str,
    name: str,
    iteration: int,
    views: List[Camera],
    gaussians: GaussianModel,
    pipeline,
    background: torch.Tensor,
    kernel_size: float,
    filter_mesh: bool,
    texture_mesh: bool,
    near: float,
    far: float,
    alpha_threshold: float,
    tetra_scale_multiplier: float,
    gaussian_scale_multiplier: float,
    filter3d_multiplier: float,
    binary_steps: int,
):
    render_path = Path(model_path) / name / f"ours_{iteration}" / "fusion"
    render_path.mkdir(parents=True, exist_ok=True)

    points, points_scale = get_tetra_points_with_multiplier(
        gaussians,
        views,
        tetra_scale_multiplier=tetra_scale_multiplier,
        near=near,
        far=far,
    )
    cells_path = render_path / "cells.pt"
    if cells_path.exists():
        print("기존 cells.pt를 읽는다.")
        cells = torch.load(cells_path)
    else:
        print("cells를 생성하고 저장한다.")
        cells = cpp.triangulate(points)
        torch.save(cells, cells_path)

    alpha = evaluate_alpha(points, views, gaussians, pipeline, background, kernel_size)
    vertices = points.cuda()[None]
    tets = cells.cuda().long()

    print(vertices.shape, tets.shape, alpha.shape)

    def alpha_to_sdf(alpha_values: torch.Tensor) -> torch.Tensor:
        return (alpha_values - alpha_threshold)[None]

    sdf = alpha_to_sdf(alpha)
    torch.cuda.empty_cache()
    verts_list, scale_list, faces_list, _ = marching_tetrahedra(vertices, tets, sdf, points_scale[None])
    torch.cuda.empty_cache()

    end_points, end_sdf = verts_list[0]
    end_scales = scale_list[0]

    faces = faces_list[0].cpu().numpy()
    left_points = end_points[:, 0, :]
    right_points = end_points[:, 1, :]
    left_sdf = end_sdf[:, 0, :]
    right_sdf = end_sdf[:, 1, :]
    left_scale = end_scales[:, 0, 0]
    right_scale = end_scales[:, 1, 0]
    distance = torch.norm(left_points - right_points, dim=-1)
    scale = left_scale + right_scale

    for step in range(binary_steps):
        print(f"binary search in step {step}")
        mid_points = (left_points + right_points) / 2
        alpha = evaluate_alpha(mid_points, views, gaussians, pipeline, background, kernel_size)
        mid_sdf = alpha_to_sdf(alpha).squeeze().unsqueeze(-1)

        ind_low = ((mid_sdf < 0) & (left_sdf < 0)) | ((mid_sdf > 0) & (left_sdf > 0))

        left_sdf[ind_low] = mid_sdf[ind_low]
        right_sdf[~ind_low] = mid_sdf[~ind_low]
        left_points[ind_low.flatten()] = mid_points[ind_low.flatten()]
        right_points[~ind_low.flatten()] = mid_points[~ind_low.flatten()]

        if step != binary_steps - 1:
            continue

        points = (left_points + right_points) / 2
        if texture_mesh:
            _, color = evaluate_alpha(
                points,
                views,
                gaussians,
                pipeline,
                background,
                kernel_size,
                return_color=True,
            )
            vertex_colors = (color.cpu().numpy() * 255).astype(np.uint8)
        else:
            vertex_colors = None

        mesh = trimesh.Trimesh(
            vertices=points.cpu().numpy(),
            faces=faces,
            vertex_colors=vertex_colors,
            process=False,
        )

        if filter_mesh:
            mask = (distance <= scale).cpu().numpy()
            face_mask = mask[faces].all(axis=1)
            mesh.update_vertices(mask)
            mesh.update_faces(face_mask)

        mesh_path = render_path / f"mesh_binary_search_{step}.ply"
        mesh.export(mesh_path)
        print(f"mesh 저장 완료: {mesh_path}")

    summary = {
        "model_path": str(model_path),
        "iteration": int(iteration),
        "alpha_threshold": float(alpha_threshold),
        "tetra_scale_multiplier": float(tetra_scale_multiplier),
        "binary_steps": int(binary_steps),
        "near": float(near),
        "far": float(far),
        "gaussian_scale_multiplier": float(gaussian_scale_multiplier),
        "filter3d_multiplier": float(filter3d_multiplier),
        "filter_mesh": bool(filter_mesh),
        "texture_mesh": bool(texture_mesh),
        "tetra_points": int(vertices.shape[1]),
        "tetra_cells": int(tets.shape[0]),
        "mesh_path": str(render_path / f"mesh_binary_search_{binary_steps - 1}.ply"),
    }
    (render_path / "parametric_mesh_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def extract_mesh(dataset: ModelParams, args, pipeline: PipelineParams) -> None:
    with torch.no_grad():
        gaussians = GaussianModel(dataset.sh_degree)
        scene = Scene(dataset, gaussians, load_iteration=args.iteration, shuffle=False)
        gaussians.load_ply(
            os.path.join(dataset.model_path, "point_cloud", f"iteration_{args.iteration}", "point_cloud.ply")
        )
        apply_proxy_multipliers(
            gaussians,
            gaussian_scale_multiplier=args.gaussian_scale_multiplier,
            filter3d_multiplier=args.filter3d_multiplier,
        )

        bg_color = [1, 1, 1] if dataset.white_background else [0, 0, 0]
        background = torch.tensor(bg_color, dtype=torch.float32, device="cuda")
        cams = scene.getTrainCameras()
        marching_tetrahedra_with_binary_search(
            dataset.model_path,
            "test",
            args.iteration,
            cams,
            gaussians,
            pipeline,
            background,
            dataset.kernel_size,
            args.filter_mesh,
            args.texture_mesh,
            args.near,
            args.far,
            args.alpha_threshold,
            args.tetra_scale_multiplier,
            args.gaussian_scale_multiplier,
            args.filter3d_multiplier,
            args.binary_steps,
        )


def main() -> None:
    parser = ArgumentParser(description="GOF mesh extraction 파라미터 sweep용 extractor")
    model = ModelParams(parser, sentinel=True)
    pipeline = PipelineParams(parser)
    parser.add_argument("--iteration", default=30000, type=int)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--filter_mesh", action="store_true")
    parser.add_argument("--texture_mesh", action="store_true")
    parser.add_argument("--near", default=0.02, type=float)
    parser.add_argument("--far", default=1e6, type=float)
    parser.add_argument("--alpha-threshold", default=0.5, type=float)
    parser.add_argument("--tetra-scale-multiplier", default=3.0, type=float)
    parser.add_argument("--gaussian-scale-multiplier", default=1.0, type=float)
    parser.add_argument("--filter3d-multiplier", default=1.0, type=float)
    parser.add_argument("--binary-steps", default=8, type=int)

    args = get_combined_args(parser)
    print("Rendering " + args.model_path)
    print(f"alpha_threshold: {args.alpha_threshold}")
    print(f"tetra_scale_multiplier: {args.tetra_scale_multiplier}")
    print(f"gaussian_scale_multiplier: {args.gaussian_scale_multiplier}")
    print(f"filter3d_multiplier: {args.filter3d_multiplier}")
    print(f"binary_steps: {args.binary_steps}")

    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)
    torch.cuda.set_device(torch.device("cuda:0"))

    extract_mesh(model.extract(args), args, pipeline.extract(args))


if __name__ == "__main__":
    main()
