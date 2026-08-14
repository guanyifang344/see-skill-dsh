#!/usr/bin/env python3
"""Install the see skill for DeepSeek Harness (DSH).

Copies this skill bundle into a DSH skill root and upserts the
"do not refuse vision" rule into the DSH instruction file:

    user:    ~/.dsh/skills/see          + rule in ~/.dsh/AGENTS.md
    project: <projectRoot>/.dsh/skills/see + rule in <projectRoot>/AGENTS.md

DSH's skill-filesystem provider discovers <root>/<name>/SKILL.md, and
dsh-agent-instructions injects AGENTS.md into every session, so these two
writes make the skill model-visible (catalog + /see gesture) and stop
text-only models from refusing to look at media.

Provider / API-key configuration stays with onboard.py — run it in your own
terminal (it needs a TTY for hidden key input):
    python3 scripts/onboard.py
"""

import argparse
import shutil
import sys
from pathlib import Path

import onboard  # reuses SEE_AGENTS_RULE / upsert / install helpers

SKILL_NAME = "see"


def project_root(start: Path) -> Path:
    for directory in [start, *start.parents]:
        if (directory / ".git").exists():
            return directory
    return start


def skill_source() -> Path:
    # scripts/.. is the skill bundle directory (contains SKILL.md).
    return Path(__file__).resolve().parent.parent


def copy_skill(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".runtime", "*.pyc"),
    )


def remove_rule_from(text: str) -> str:
    cleaned = onboard.SEE_AGENTS_PATTERN.sub("", text).strip()
    return cleaned + "\n" if cleaned else ""


def status_report(target: Path, agents: Path | None) -> None:
    installed = target.is_dir() and (target / "SKILL.md").is_file()
    print(f"技能目录：{target} —— {'已安装' if installed else '未安装'}")
    if agents:
        text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
        print(f"拒绝覆盖规则：{agents} —— {'已写入' if onboard.agents_rule_installed(text) else '未写入'}")
    if not installed:
        print(f"运行 python3 {skill_source() / 'scripts' / 'install_dsh.py'} 安装。")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="将 see skill 安装到 DeepSeek Harness。")
    root_group = parser.add_mutually_exclusive_group()
    root_group.add_argument(
        "--root",
        choices=["user", "project"],
        default="user",
        help="安装到用户级 ~/.dsh/skills（默认）或项目级 <项目根>/.dsh/skills。",
    )
    root_group.add_argument(
        "--dir",
        default="",
        help="自定义技能根目录（测试 / 离线部署用，规则仍写入 ~/.dsh/AGENTS.md）。",
    )
    parser.add_argument("--no-agents", action="store_true", help="不写 AGENTS.md 拒绝覆盖规则。")
    parser.add_argument("--status", action="store_true", help="只显示安装与配置状态。")
    parser.add_argument("--uninstall", action="store_true", help="移除技能目录与 AGENTS 规则。")
    args = parser.parse_args()

    project = project_root(Path.cwd())
    if args.dir:
        root = Path(args.dir).expanduser()
        agents = None if args.no_agents else Path.home() / ".dsh" / "AGENTS.md"
    elif args.root == "project":
        root = project / ".dsh" / "skills"
        agents = None if args.no_agents else project / "AGENTS.md"
    else:
        root = Path.home() / ".dsh" / "skills"
        agents = None if args.no_agents else Path.home() / ".dsh" / "AGENTS.md"
    target = root / SKILL_NAME

    if args.status:
        status_report(target, agents)
        return onboard.config_status()

    if args.uninstall:
        removed_skill = False
        if target.is_dir():
            shutil.rmtree(target)
            removed_skill = True
        print(f"技能目录：{'已移除' if removed_skill else '不存在'}（{target}）")
        if agents and agents.is_file():
            text = agents.read_text(encoding="utf-8")
            if onboard.agents_rule_installed(text):
                cleaned = remove_rule_from(text)
                if cleaned:
                    agents.write_text(cleaned, encoding="utf-8")
                else:
                    agents.unlink()
                print(f"拒绝覆盖规则：已移除（{agents}）")
            else:
                print(f"拒绝覆盖规则：不存在（{agents}）")
        return 0

    source = skill_source()
    if source.resolve() == target.resolve():
        print(f"已在目标位置：{target}，跳过复制。")
    else:
        if not (source / "SKILL.md").is_file():
            print(f"[ERROR] 未找到 {source / 'SKILL.md'}；请从 skill 包内运行本脚本。", file=sys.stderr)
            return 1
        copy_skill(source, target)
        print(f"已安装：{target}")
    if agents and not args.no_agents:
        path, changed = onboard.install_agents_rule(agents)
        print(f"{'已写入' if changed else '已存在'}拒绝覆盖规则：{path}")
    print()
    print("下一步：")
    print("  1. 配置供应商（在你自己的终端运行）：python3 scripts/onboard.py")
    print("  2. 或使用环境变量：export SEE_PROVIDER=zenmux 与对应 *_API_KEY。")
    print("  3. 新会话即生效；已打开的会话在目录刷新后可见，必要时新开一个会话。")
    print("  4. 发本地路径或 URL 给模型，如：使用 see 查看 /path/to/screenshot.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
