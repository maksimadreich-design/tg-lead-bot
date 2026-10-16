import re

with open("yt_page.txt", "r", encoding="utf-8") as f:
    text = f.read()

title_m = re.search(r'<title>(.*?)</title>', text)
desc_m = re.search(r'"shortDescription":"(.*?)"', text)

with open("yt_result.txt", "w", encoding="utf-8") as out:
    out.write("TITLE: " + (title_m.group(1) if title_m else "") + "\n\n")
    out.write("DESC: " + (desc_m.group(1) if desc_m else "") + "\n")

print("Saved to yt_result.txt")
