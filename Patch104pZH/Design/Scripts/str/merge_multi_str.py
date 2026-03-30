from pathlib import Path
import os


def build_abs_path(relative_path: str) -> Path:
    dir: str = os.path.dirname(os.path.realpath(__file__))
    return Path(dir).joinpath(relative_path).absolute()


def startswith_nocase(s: str, startswith: str) -> bool:
    return s.lower().startswith(startswith.lower())


def run():
    generals_str_statusquo = build_abs_path("../../../GameFilesEdited/Data/generals.str.statusquo") # manually create a copy of the source file
    generals_str_upgrade = build_abs_path("../../../GameFilesEdited/Data/generals.str.upgrade")
    generals_str_new = build_abs_path("../../../GameFilesEdited/Data/generals.str")

    assert generals_str_statusquo.is_file(), "Statusquo file not found!"
    assert generals_str_upgrade.is_file(), "Upgrade file not found!"

    with open(generals_str_statusquo, mode="r", encoding="utf-8") as file:
        statusquo_lines = file.readlines()

    with open(generals_str_upgrade, mode="r", encoding="utf-8") as file:
        upgrade_lines = file.readlines()

    #upgrade_languages = ["US:", "DE:", "FR:", "ES:", "IT:", "KO:", "ZH:", "BP:", "PL:", "RU", "AR", "UK", "SV", "HE"]
    upgrade_languages = ["US:", "DE:", "FR:", "ES:", "IT:", "KO:", "ZH:", "BP:", "PL:", "RU:", "SV:", "HE:"]

    # --- 1. Map all labels in the UPGRADE file ---
    upgrade_label_index_map = dict[str, int]()
    is_in_label_block = False

    for index, line in enumerate(upgrade_lines):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("//"):
            continue
        elif not is_in_label_block:
            if ":" in stripped_line and not startswith_nocase(stripped_line, "End"):
                is_in_label_block = True
                upgrade_label_index_map[stripped_line] = index
        elif startswith_nocase(stripped_line, "End"):
            is_in_label_block = False

    # --- 2. Process STATUSQUO file and inject ---
    new_lines = list[str]()
    is_in_label_block = False
    label_name = ""
    sub_label_name = ""

    for original_line in statusquo_lines:
        stripped_line = original_line.strip()

        # Keep empty lines
        if not stripped_line:
            new_lines.append(original_line)
            continue

        # Handle comments and patch tags
        if stripped_line.startswith("//"):
            if "patch104p-core-begin" in stripped_line or "patch104p-optional-begin" in stripped_line:
                sub_label_name = stripped_line
            elif "patch104p-core-end" in stripped_line or "patch104p-optional-end" in stripped_line:
                sub_label_name = ""
            new_lines.append(original_line)
            continue

        # Detect Label Start
        if not is_in_label_block:
            if ":" in stripped_line and not startswith_nocase(stripped_line, "End"):
                is_in_label_block = True
                label_name = stripped_line
            new_lines.append(original_line)
            continue

        # Detect Label End
        if startswith_nocase(stripped_line, "End"):
            is_in_label_block = False
            sub_label_name = ""
            new_lines.append(original_line)
            continue

        # Check if it's a translation line
        upgrade_language = ""
        for language in upgrade_languages:
            if stripped_line.startswith(language):
                upgrade_language = language
                break

        if upgrade_language:
            # === THE PROTECTION LOGIC ===
            # DO NOT TOUCH CORE BLOCKS!
            if sub_label_name == "//patch104p-core-begin":
                new_lines.append(original_line)
                continue

            # We are in Optional block (or normal block). Let's search for an upgrade!
            index = upgrade_label_index_map.get(label_name, -1)
            updated_line = original_line

            if index >= 0:
                upgrade_index = index + 1
                found_upgrade_line = ""
                fallback_upgrade_line = ""
                upgrade_sub_label_name = ""

                while upgrade_index < len(upgrade_lines):
                    u_line_orig = upgrade_lines[upgrade_index]
                    u_line_stripped = u_line_orig.strip()

                    if startswith_nocase(u_line_stripped, "End"):
                        break

                    if u_line_stripped.startswith("//"):
                        if "patch104p-core-begin" in u_line_stripped or "patch104p-optional-begin" in u_line_stripped:
                            upgrade_sub_label_name = u_line_stripped
                        elif "patch104p-core-end" in u_line_stripped or "patch104p-optional-end" in u_line_stripped:
                            upgrade_sub_label_name = ""
                        upgrade_index += 1
                        continue

                    if u_line_stripped.startswith(upgrade_language):
                        # 1. Perfect Match (Optional maps to Optional)
                        if upgrade_sub_label_name == sub_label_name:
                            found_upgrade_line = u_line_stripped
                            break
                        # 2. Fallback: If Upgrade file doesn't use sub-labels, grab what's there
                        elif upgrade_sub_label_name == "":
                            fallback_upgrade_line = u_line_stripped

                    upgrade_index += 1

                # Decide which line to use (Prefer perfect match, fallback if needed)
                final_line_to_inject = found_upgrade_line if found_upgrade_line else fallback_upgrade_line

                if final_line_to_inject:
                    # Preserve original file's indentation
                    leading_spaces = original_line[:len(original_line) - len(original_line.lstrip())]
                    updated_line = f"{leading_spaces}{final_line_to_inject}\n"

            new_lines.append(updated_line)
        else:
            # Not a language line, keep original
            new_lines.append(original_line)

    with open(generals_str_new, mode="w", encoding="utf-8") as file:
        for line in new_lines:
            file.write(line.rstrip('\n') + '\n')

    print("Process complete! Generates updated generals.str file.")

if __name__ == "__main__":
    run()