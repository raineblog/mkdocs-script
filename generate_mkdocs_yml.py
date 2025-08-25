import toc
import json
import yaml

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

if __name__ == "__main__":
    info = load_json('info.json')
    template = info['project'] | toc.parse_yaml('script/template.yml')
    template['nav'] = toc.get_site_nav()
    with open('mkdocs.yml', 'w', encoding='utf-8') as file:
        yaml.dump(template, file, allow_unicode=True, indent=4, sort_keys=False)
