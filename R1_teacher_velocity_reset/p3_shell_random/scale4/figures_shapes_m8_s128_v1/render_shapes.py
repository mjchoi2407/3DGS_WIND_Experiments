"""검산된 자연 응답의 선택 시각 형상을 물리 길이의 같은 축척으로 그린다."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np

from wind3dgs.evaluation.teacher_p3_shell_random import QUALITY, file_identity, inspect_run
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame
from wind3dgs.teacher.p3_shell import P3Shell


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("기존 그림을 덮어쓸 수 없습니다")
    config, _ = inspect_run(args.run)
    audit = json.loads(args.verification.read_text())
    assert audit["verified"] and audit["run"] == args.run.name
    assert audit["manifest_sha256"] == file_identity(args.run / "manifest.json")["sha256"]
    assert config["start_frame"] == 0 and config["end_frame"] == 90
    model = P3Shell(config["resolution"], diagonal=config["diagonal"])
    xx, yy = np.meshgrid(np.linspace(.25, 1., 65), np.linspace(0., 1., 65))
    surface = model.moving_surface_map(np.column_stack((xx.ravel(), yy.ravel())))
    rest = np.column_stack((xx.ravel(), np.zeros(xx.size), .5 - yy.ravel()))
    peak_frame = max(audit["frame_results"], key=lambda f: f["max_nodal_displacement_m"])["frame"]
    peak, _ = load_frame(args.run, peak_frame)
    peak_step = int(np.linalg.norm(peak["u_m"], axis=-1).max(axis=1).argmax())
    selections = [(0, 0, "Rest"), (17, config["substeps"], "0.3초"),
                  (41, config["substeps"], "0.7초"), (65, config["substeps"], "1.1초"),
                  (89, config["substeps"], "1.5초"), (peak_frame, peak_step, "최대 nodal 변위 시각")]
    states, provenance = [], []
    for frame, index, title in selections:
        trace, _ = load_frame(args.run, frame)
        displacement = surface @ trace["u_m"][index]
        states.append((rest + displacement, displacement[:, 1], title, float(trace["time_s"][index])))
        provenance.append({"frame": frame, "substep": index, "time_s": float(trace["time_s"][index]),
                           "title": title, "frame_sha256": file_identity(args.run / "frames" / f"{frame:03d}.npz")["sha256"]})
    limit = max(float(abs(row[1]).max()) for row in states)
    norm = Normalize(-max(limit, 1e-15) * 1000, max(limit, 1e-15) * 1000)
    cmap = plt.get_cmap("coolwarm")
    plt.rcParams.update({"font.family": "Noto Sans CJK KR", "axes.unicode_minus": False, "font.size": 9})
    fig = plt.figure(figsize=(12, 8), layout="constrained")
    axes = []
    for i, (position, displacement, title, time_s) in enumerate(states):
        ax = fig.add_subplot(2, 3, i + 1, projection="3d")
        axes.append(ax)
        shape = xx.shape
        ax.plot_surface(position[:, 0].reshape(shape), position[:, 2].reshape(shape),
                        position[:, 1].reshape(shape), facecolors=cmap(norm(displacement.reshape(shape) * 1000)),
                        rstride=2, cstride=2, linewidth=0, shade=False)
        fixed_x, fixed_z = np.meshgrid([0., .25], [-.5, .5])
        ax.plot_surface(fixed_x, fixed_z, np.zeros_like(fixed_x), color=".65", alpha=.7)
        ax.set(xlim=(0, 1), ylim=(-.5, .5), zlim=(-.5, .5), xlabel="x (m)", ylabel="z (m)",
               zlabel="y (m)", title=f"{title}\n{time_s:.6f} s")
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=22, azim=-65)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=axes, shrink=.6,
                 label="초기 법선 방향 변위 (mm)")
    fig.suptitle(f"P3 자연 응답 · 바람 {config['wind_scale']:g}배 · n{config['resolution']}/sub{config['substeps']}\n"
                 "세 축 동일 축척 · 변위 확대 없음 · 회색은 고정 영역 · 공간/시간 수렴 판정은 별도")
    args.output.mkdir(parents=True)
    for extension in ("png", "pdf"):
        fig.savefig(args.output / ("natural_shapes." + extension), dpi=170)
    plt.close(fig)
    report = {"run": args.run.name, "manifest_sha256": audit["manifest_sha256"],
              "verification_sha256": file_identity(args.verification)["sha256"],
              "script_sha256": file_identity(Path(__file__))["sha256"], "states": provenance,
              "displacement_scale": 1, "equal_axis_scale": True, **QUALITY}
    (args.output / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("검산 원본의 선택 시각 형상 그림 저장 완료", flush=True)


if __name__ == "__main__":
    main()
