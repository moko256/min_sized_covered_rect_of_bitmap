## Purpose
On the environment which provides only drawing rect (e.g. Stormworks), we can optimize drawing bitmap by drawing pixels with rectangle at once.
The purpose of this repository is optimizing that problem.

## Steps
- Convert a bitmap to paths.
- Convert paths to rectangle paths with this algorithm: ["Minimum Partitioning of Rectilinear Regions"](https://cir.nii.ac.jp/crid/1050282812867071360)

## Status
This repository isn't ready for work.
