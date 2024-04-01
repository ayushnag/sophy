###### MAP SETUP ######


# packages needed to make map:
import os                                              # for file paths
import pandas                as pd
import numpy                 as np
import xarray                as xr                     # to load bathymetry data
from   datetime              import date               # for saving figures with today's date

import matplotlib
import matplotlib.pyplot     as plt                    # needed to make map setup
import matplotlib.path       as mpath                  # to draw circle for map
import matplotlib.patches    as mpatches               # to draw boxes on map  
from mpl_toolkits.axes_grid1 import make_axes_locatable

import cmocean.cm            as cmo                    # to add colorbars
import cartopy                                         # to make map
import cartopy.crs           as     ccrs               # for map projection
import cartopy.feature       as     cfeature           # to add land features to map
from   scipy.ndimage         import gaussian_filter    # for adding bathymetry
import shapefile

import geopandas             as     gpd                # for adding shapefiles of frontal zones 
import pyproj
from   osgeo                 import gdal

import scipy.io                                        # to load matlab files
import glob                                            # to pick files from folder

# os.chdir('/Users/hannah/Documents/UW-PMEL/Research/so_cflux_spcomp_repo/')




############################################################################
######  LOAD FRONT DATA FOR MAP  ###########################################
############################################################################

# # bathymetry
# filepath = '/Users/hannah/Documents/UW-PMEL/Research/eScience_Data_Science_Postdoc_Fellowship_repo/data/01_raw/'
# co2_clim = xr.open_dataset(os.path.join(filepath,'MPI-ULB-SOM_FFN_clim.nc'))





############################################################################
######  SET COLORS, FONT SIZES, ETC FOR MAP  ###############################
############################################################################


#### FIGURE SIZE
fig_width  = 6   # inches
fig_height = 6   # inches

#### FONT SIZES
fontsize_large  = 8
fontsize_medium = 6
fontsize_small  = 4

#### MARKER AND LINE SIZES
markersize     = 1
axis_linewidth = 2

#### PLOT COLORS
plot_facecolor          = '#E9F5F5'  # '#E6F1F1'
overplot_label_color    = '#7B878F'
darker_label_color      = '#C9CCD4'
background_poster_color = '#14417C'
box_color               = '#FA5BBB'

poster_text_color = '#B1BED1'


plt.rcParams["axes.edgecolor"] = overplot_label_color
plt.rcParams["axes.linewidth"] = axis_linewidth
# plt.figure(facecolor='none') 

plt.rcParams['axes.facecolor'] = plot_facecolor
# plt.rcParams['fig.facecolor'] = 'none'



############################################################################
######  Set up Southern Ocean Map  #########################################
############################################################################

map_proj  = ccrs.SouthPolarStereo()
text_proj = ccrs.PlateCarree()

def map_southern_ocean_axes_setup(
    ax:                    matplotlib.axes.Axes,
    fig:                   matplotlib.figure.Figure,
    max_latitude:          float = -30,
    add_gridlines:         bool  = False,
    color_land:            bool  = True,
    land_edgecolor:        str   = overplot_label_color,
    land_facecolor:        str   = overplot_label_color,
    fontsize:              float = 4,
    map_facecolor:         str   = plot_facecolor,
    coast_linewidth:       float = 0.25,
    gridlines_linewidth:   float = 0.25,
    girdlines_color:       str   = 'grey',
    gridlines_alpha:       float = 0.1,
    longitude_label_color: str   = darker_label_color,
    latitude_label_color:  str   = darker_label_color
) -> None:
    """
    This function sets up the subplot so that it is a cartopy map of the Southern Ocean.
    returns void as the ax and figure objects are pointers not data.
    Args:
        ax  (matplotlib.axes.Axes):     The axis object to add the map to.
        fig (matplotlib.figure.Figure): The figure object for the figure in general.
        add_gridlines (bool):           Whether or not to add gridlines to the plot.
    """
    
    
    ### Limit the map to -40 degrees latitude and below.
    ax.set_extent([-180, 180, -90, max_latitude+0.6], ccrs.PlateCarree())  # set to -29.4 for map out to 30 degrees or -39.4 for map out to 40 degrees
   
    ### Tune the subplot layout
    fig.subplots_adjust(bottom=0.05, top=0.95, left=0.04, right=0.95, wspace=0.02)
    
    ### Make the background of the plot white
    ax.set_facecolor(map_facecolor)

    ### Make SO plot boundary a circle
    def plot_circle_boundary() -> None:
        """
        Make SO plot boundary a circle.
        Compute a circle in axes coordinates, which we can use as a boundary for the map.
        We can pan/zoom as much as we like - the boundary will be permanently circular.
        """
        theta  = np.linspace(0, 2 * np.pi, 100)
        center, radius = [0.5, 0.5], 0.5  ## could use 0.45 here, as Simon Thomas did
        verts  = np.vstack([np.sin(theta), np.cos(theta)]).T
        circle = mpath.Path(verts * radius + center)
        ax.set_boundary(circle, transform = ax.transAxes)

    plot_circle_boundary()


    ### Add gridlines (if True)
    if add_gridlines:
        # ax.gridlines(color = girdlines_color, alpha = gridlines_alpha, linewidth = gridlines_linewidth)
        
        # specifying xlocs/ylocs yields number of meridian/parallel lines
        dmeridian = 60  # spacing for lines of meridian
        dparallel = 20  # spacing for lines of parallel -- can change this to 10
        num_merid = int(360/dmeridian + 1)
        num_parra = int(180/dparallel + 1)
        gl = ax.gridlines(crs=ccrs.PlateCarree(), 
                          xlocs=np.linspace(-180, 180, num_merid), 
                          ylocs=np.linspace(-80,  -30, 6),  # np.linspace(-90,  -30, num_parra), 
                          linestyle=(0, (10, 5)), linewidth=gridlines_linewidth, color='grey', alpha=gridlines_alpha) # linestyle: (offset, (line pt, space pt))
        
        # for label alignment
        va = 'center' # also bottom, top
        ha = 'center' # right, left
        degree_symbol = u'\u00B0'

        # for locations of (meridional/longitude) labels
        lond = np.linspace(-180, 180, num_merid)
        latd = np.zeros(len(lond))

        for (alon, alat) in zip(lond, latd):
            projx1, projy1 = ax.projection.transform_point(alon, max_latitude-2.5, ccrs.Geodetic())  # set to -29 for map out to 30 degrees or -39 for a map out to 40 degrees
            if alon>-180 and alon<-100:  # -120 degrees
                ha = 'left'
                va = 'center_baseline'
            if alon>-100 and alon<0:  # -60 degrees
                ha = 'left'
                va = 'top'
            if alon>0 and alon<100:   # 60 degrees
                ha = 'right'
                va = 'bottom'
            if alon>100 and alon<180:   # 120 degrees
                ha = 'center'
                va = 'baseline'
            if np.abs(alon-0)<0.01:
                ha = 'left'
                va = 'center'
            if alon==-180:
                ha = 'left'
                va = 'top'
            if (alon<180):
                txt =  ' {0}'.format(str(int(alon)))+degree_symbol
                ax.text(projx1, projy1, txt, va=va, ha=ha, color=latitude_label_color, fontsize=fontsize, zorder=8)
                
        # for locations of (meridional/longitude) labels select longitude: 315 for label positioning
        lond2 = 60*np.ones(len(lond))
        latd2 = np.linspace(-70,  -30, 5) # np.linspace(-90, 90, num_parra)
        va, ha = 'center', 'center'
        for (alon, alat) in zip(lond2, latd2):
            projx1, projy1 = ax.projection.transform_point(alon-176, alat-3, ccrs.Geodetic())
            txt =  '{0}'.format(str(int(alat)))+degree_symbol
            ax.text(projx1, projy1, txt, va=va, ha=ha, color=longitude_label_color, fontsize=fontsize, zorder=8)
        
        
    ### Add in coastlines/features
    if color_land:
        ax.add_feature(cfeature.LAND, zorder=1, linewidth = coast_linewidth, edgecolor=land_edgecolor, facecolor=land_facecolor)
    else:
        ax.coastlines(resolution = "50m", zorder=1, linewidth = coast_linewidth)




############################################################################
######  Add Fronts to Map  #################################################
############################################################################

def add_fronts(    
    ax: matplotlib.axes.Axes,
    add_labels:        bool  = False,
    front_color_theme: str   = 'blues',
    front_linewidth:   float = 0.25,
    fontsize:          float = 4,
) -> None:
    """
    Add fronts to SO map. Fronts were defined by Hanna Rosenthal using Saildrone August 2019 data
        Args:
        ax  (matplotlib.axes.Axes): The axis object to add the fronts to.
    """
    
    ######  Front data  #######################################################
# '/Users/hannah/Documents/UW-PMEL/Research/sophy_main_repo/sophy/data/shapefiles/fronts'
# '/Users/hannah/Documents/UW-PMEL/Research/sophy_main_repo/sophy/sophy/transformations'
    so_fronts = shapefile.Reader('../../data/shapefiles/fronts/so_fronts.shp')
    # stf_mod   = shapefile.Reader('../../data/shapefiles/fronts/stf_mod/stf_mod.shp')

    stf  = so_fronts.shape(0).points
    saf  = so_fronts.shape(1).points
    pf   = so_fronts.shape(2).points
    sacc = so_fronts.shape(3).points
    sie  = so_fronts.shape(4).points
    
    
    
    ######  Front colors  ####################################################### 

    # Dictionary with colors
    if front_color_theme == 'blues':
        front_colors = {'STF':'#133c55', 'SAF':'#386fa4', 'PF':'#59a5d8','SACCF':'#84d2f6', 'SIE':'#91e5f6'}
    if front_color_theme == 'greys':
        front_colors = {'STF':'#666666', 'SAF':'#999999', 'PF':'#aaaaaa','SACCF':'#bbbbbb', 'SIE':'#cccccc'}
    
    
    
    ######  Add patches  #######################################################    
    
    stf_patch  = plt.Polygon(stf,  fill=False, linewidth=front_linewidth, edgecolor=front_colors['STF'],                                                 zorder=5)
    saf_patch  = plt.Polygon(saf,  fill=False, linewidth=front_linewidth, edgecolor=front_colors['SAF'],                                                 zorder=4)
    pf_patch   = plt.Polygon(pf,   fill=False, linewidth=front_linewidth, edgecolor=front_colors['PF'],                                                  zorder=3)
    sacc_patch = plt.Polygon(sacc, fill=False, linewidth=front_linewidth, edgecolor=front_colors['SACCF'],                                               zorder=2)
    sie_patch  = plt.Polygon(sie,  fill=True,  linewidth=front_linewidth,   edgecolor=front_colors['SIE'],  facecolor=front_colors['SIE'], alpha=0.4, zorder=0)
    
    ax.add_patch(stf_patch)
    ax.add_patch(saf_patch)
    ax.add_patch(pf_patch)
    ax.add_patch(sacc_patch)
    ax.add_patch(sie_patch)
    
    
    # Label the fronts (if True)
    if add_labels:
        ax.annotate('STF',   xy=(   5, -40),   color=front_colors['STF'],   size = fontsize, xycoords=ccrs.PlateCarree()._as_mpl_transform(ax)) 
        ax.annotate('SAF',   xy=(   3, -44.5), color=front_colors['SAF'],   size = fontsize, xycoords=ccrs.PlateCarree()._as_mpl_transform(ax)) 
        ax.annotate('PF',    xy=(   1, -49),   color=front_colors['PF'],    size = fontsize, xycoords=ccrs.PlateCarree()._as_mpl_transform(ax)) 
        ax.annotate('SACCF', xy=(72.5, -58.5), color=front_colors['SACCF'], size = fontsize, xycoords=ccrs.PlateCarree()._as_mpl_transform(ax)) 
        ax.annotate('SIE',   xy=(17.5, -55.4), color=front_colors['SIE'],   size = fontsize, xycoords=ccrs.PlateCarree()._as_mpl_transform(ax)) 
    
