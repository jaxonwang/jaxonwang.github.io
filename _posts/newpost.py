import sys
import collections
import datetime

from dateutil.tz import tzlocal

default_attrs = collections.OrderedDict([
    ("layout", "post"),
    ("title", None),
    ("date", None),
    ("categories", None),
    ("tags", None),
     ])


def attrs_to_yml(attrs):
    tmp = []
    for key, value in attrs.items():
        line = key + ": " + (value if value else "")
        tmp.append(line)
    return "\n".join(tmp)


def main():
    title_words = sys.argv[1:]
    title = " ".join(title_words)

    default_attrs["title"] = "\"" + title + "\""
    now = datetime.datetime.now(tzlocal())
    default_attrs["date"] = now.strftime("%Y-%m-%d %H:%M:%S %z")
    file_name = now.strftime("%Y-%m-%d-") + "-".join(title_words) + ".md"

    with open(file_name, "w") as f:
        f.write("---\n")
        f.write(attrs_to_yml(default_attrs))
        f.write("\n---\n")

    print(file_name)

if __name__ == "__main__":
    main()

