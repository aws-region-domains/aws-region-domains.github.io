import json
import os
from datetime import datetime

import botocore
import whois

EXTRA_REGIONS = [
    {
        'name': 'ap-southeast-7',
        'description': 'Asia Pacific (Thailand)',
    },
]

def _parse_whois_date(whois_date):
    if isinstance(whois_date, list):
        whois_date = whois_date[0]
    return datetime.strftime(whois_date, '%Y-%m-%d') if whois_date else None


def get_whois_info(region_code: str, region_description: str):
    # Here we try to simulate a domain-like format from the region name
    domain = f'{region_code}.com'

    # Get WHOIS info using python-whois
    try:
        w = whois.whois(domain)

        # Extract relevant details
        info = {
            'domain': domain,
            'region': region_code,
            'description': region_description,
            'registrar': w.registrar if 'registrar' in w else None,
            'creation_date': _parse_whois_date(w.creation_date),
            'updated_date': _parse_whois_date(w.updated_date),
            'expiry_date': _parse_whois_date(w.expiration_date),
            'status': w.status if 'status' in w else None,
        }
        print(f'Successfully retrieved WHOIS info for {domain}')

        return info
    except Exception as e:
        print(f'Error getting WHOIS info for {domain}: {e}')
        return None


def main():
    botocore_dir = os.path.dirname(botocore.__file__)

    partitions_file_path = os.path.join(botocore_dir, 'data', 'partitions.json')

    with open(partitions_file_path, 'r', encoding='utf-8') as file:
        partitions_data = json.load(file)

    partitions = partitions_data['partitions']
    regions = [
        {
            'name': region_name,
            'description': region_detail['description'],
        }
        for partition in partitions
        for region_name, region_detail in partition['regions'].items()
        if not region_name.endswith('-global')
    ]

    for extra_region in EXTRA_REGIONS:
        if not any(region['name'] == extra_region['name'] for region in regions):
            regions.append(extra_region)

    with open('docs/aws-regions.json', 'w', encoding='utf-8') as f:
        json.dump(regions, f, indent=4)

    result = []

    for region in regions:
        info = get_whois_info(region['name'], region['description'])
        if info:
            result.append(info)
        else:
            result.append({
                'domain': f'{region['name']}.com',
                'registered': False,
            })

    with open('docs/whois_info.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)

    print('WHOIS data has been written to whois_info.json.')


if __name__ == '__main__':
    main()
