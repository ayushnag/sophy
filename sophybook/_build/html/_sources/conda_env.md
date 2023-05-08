# Conda Environment Information

_Note: many elements in this guide adapted from
Ryan Abernathey's excellent
[environmental data science guide](https://earth-env-data-science.github.io/)._

## Lightweight Alternative: Miniconda

If you are installing python on a remote machine via ssh, or you simply don't
want to download a huge file like the Anaconda Python Distribution, there is a
lightweight alternative installation method.

-  **Obtain a minimal Python installer**
  We recommend the [Miniconda](https://conda.io/miniconda.html) installer;
  this provides a Python install for your operating system, plus the **conda**
  package manager. This way, you can only install the packages you *want*.

## Create environment

It is strongly recommended to read official
[Getting Started with Conda](https://conda.io/docs/user-guide/getting-started.html#)
guide.

To create a conda environment, you execute the following command:

    $ conda create -n sophyvenv datasette geopandas jupyter tqdm

## Issues
### Geopandas installation
Had issues with geopandas installation on Anaconda, switching to miniconda and using the above command worked. The geospatial packages (geopandas, fiona, cartopy, shapely, pyproj) are all finicky especially on Windows. The working solution was to only install geopandas and that installs most of the other packages
### PyTorch installation
Pytorch and Keras installation with conda-forge was unsuccessful. Had to use pip install instead.

