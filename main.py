# TensegrityPoseNormalizer prototype
# Small CLI: read simple CSV/JSON pose files, normalize to schema and write combined CSV/JSON
import sys
import argparse
import csv
import json
import math
from typing import List, Dict, Any

# Schema per record:
# {"timestamp": float, "module_id": str, "position": [x,y,z], "orientation": [qw,qx,qy,qz]}

def euler_to_quat(roll, pitch, yaw):
    # ZYX (yaw-pitch-roll) to quaternion
    cr = math.cos(roll/2)
    sr = math.sin(roll/2)
    cp = math.cos(pitch/2)
    sp = math.sin(pitch/2)
    cy = math.cos(yaw/2)
    sy = math.sin(yaw/2)
    qw = cr*cp*cy + sr*sp*sy
    qx = sr*cp*cy - cr*sp*sy
    qy = cr*sp*cy + sr*cp*sy
    qz = cr*cp*sy - sr*sp*cy
    return [qw, qx, qy, qz]

def parse_csv(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try to extract common fields. Users should adapt to their CSV column names.
            try:
                ts = float(row.get('timestamp') or row.get('time') or row.get('t'))
            except Exception:
                continue
            mid = row.get('module_id') or row.get('id') or row.get('module') or '0'
            def getf(*names, default=0.0):
                for n in names:
                    if n in row and row[n] != '':
                        try:
                            return float(row[n])
                        except Exception:
                            pass
                return default
            x = getf('x','pos_x','px')
            y = getf('y','pos_y','py')
            z = getf('z','pos_z','pz')
            qw = row.get('qw')
            if qw is not None:
                # quaternion fields
                try:
                    quat = [float(row.get('qw')), float(row.get('qx')), float(row.get('qy')), float(row.get('qz'))]
                except Exception:
                    quat = [1.0,0.0,0.0,0.0]
            else:
                # check euler
                try:
                    roll = getf('roll','r')
                    pitch = getf('pitch','p')
                    yaw = getf('yaw','y')
                    quat = euler_to_quat(roll,pitch,yaw)
                except Exception:
                    quat = [1.0,0.0,0.0,0.0]
            records.append({
                'timestamp': ts,
                'module_id': str(mid),
                'position': [x,y,z],
                'orientation': quat
            })
    return records

def parse_json(path: str) -> List[Dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    records = []
    # Accept either list of records or dict with 'frames'
    items = data if isinstance(data, list) else data.get('frames') or data.get('records') or []
    for it in items:
        try:
            ts = float(it.get('timestamp') or it.get('time'))
        except Exception:
            continue
        mid = str(it.get('module_id') or it.get('id') or '0')
        pos = it.get('position') or [it.get('x'), it.get('y'), it.get('z')]
        if pos and all(isinstance(v, (int,float)) for v in pos):
            position = [float(pos[0]), float(pos[1]), float(pos[2])]
        else:
            position = [0.0,0.0,0.0]
        ori = it.get('orientation')
        if ori and len(ori) == 4:
            orientation = [float(ori[0]),float(ori[1]),float(ori[2]),float(ori[3])]
        else:
            # try euler
            r = it.get('roll') or it.get('r') or 0.0
            p = it.get('pitch') or it.get('p') or 0.0
            y = it.get('yaw') or it.get('y') or 0.0
            orientation = euler_to_quat(float(r),float(p),float(y))
        records.append({'timestamp': ts, 'module_id': mid, 'position': position, 'orientation': orientation})
    return records

def write_json(out_path: str, records: List[Dict[str, Any]]):
    with open(out_path, 'w') as f:
        json.dump(sorted(records, key=lambda r: (r['module_id'], r['timestamp'])), f, indent=2)

def write_csv(out_path: str, records: List[Dict[str, Any]]):
    fieldnames = ['timestamp','module_id','pos_x','pos_y','pos_z','quat_w','quat_x','quat_y','quat_z']
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted(records, key=lambda r: (r['module_id'], r['timestamp'])):
            writer.writerow({
                'timestamp': r['timestamp'],
                'module_id': r['module_id'],
                'pos_x': r['position'][0],
                'pos_y': r['position'][1],
                'pos_z': r['position'][2],
                'quat_w': r['orientation'][0],
                'quat_x': r['orientation'][1],
                'quat_y': r['orientation'][2],
                'quat_z': r['orientation'][3]
            })

def main(argv):
    p = argparse.ArgumentParser(description='Normalize pose time-series to common schema')
    p.add_argument('--inputs', nargs='+', required=True, help='Input files (CSV or JSON)')
    p.add_argument('--out', required=True, help='Output file (json or csv)')
    args = p.parse_args(argv)

    all_records = []
    for path in args.inputs:
        if path.lower().endswith('.csv'):
            recs = parse_csv(path)
            print(f'Parsed {len(recs)} records from {path}')
            all_records.extend(recs)
        elif path.lower().endswith('.json'):
            recs = parse_json(path)
            print(f'Parsed {len(recs)} records from {path}')
            all_records.extend(recs)
        else:
            print(f'Skipping unknown file type: {path}')
    if args.out.lower().endswith('.json'):
        write_json(args.out, all_records)
        print(f'Wrote {len(all_records)} records to {args.out}')
    elif args.out.lower().endswith('.csv'):
        write_csv(args.out, all_records)
        print(f'Wrote {len(all_records)} records to {args.out}')
    else:
        print('Output must end with .json or .csv')

if __name__ == "__main__":
    main(sys.argv[1:])
