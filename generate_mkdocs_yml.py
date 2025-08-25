import toc
import json
import yaml

if __name__ == "__main__":
    with open('info.json', 'r', encoding='utf-8') as file:
        info = json.load(file)

    nav = info['nav']
    template = info['project'] | toc.parse_yaml('script/template.yml')

    nav_all = [
        {
            '简介': [
                'index.md',
                'intro/format.md',
                'intro/usage.md',
                'intro/discussion.md',
                'intro/setting.md',
                'madoka.md'
            ]
        }
    ]

    for item in nav:
        title = item['title']
        children = item['children']
        nav_all.append({title: children})

    template['nav'] = nav_all

    with open('mkdocs.yml', 'w', encoding='utf-8') as file:
        yaml.dump(template, file, allow_unicode=True, indent=4, sort_keys=False)
