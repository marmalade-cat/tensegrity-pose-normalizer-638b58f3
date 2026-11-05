TensegrityPoseNormalizer

A compact Python prototype that normalizes per-module pose time-series from simple CSV or JSON input files into a unified schema and exports combined CSV or JSON for replay/visualization. No dependencies (uses Python 3 standard library).

Usage:
  python3 main.py --inputs file1.csv file2.json --out output.json

The prototype assumes timestamps in seconds and positions as x,y,z. Orientations may be provided as quaternions (qw,qx,qy,qz) or Euler angles (roll,pitch,yaw) in radians; Euler will be converted to a quaternion with a simple routine. Input parsing is permissive; adapt as needed for real datasets.

This is an example-level tool — extend parsing rules for your article/supplementary formats and validate time bases before using in production.