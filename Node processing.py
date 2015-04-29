# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Least-code path node processing tool
# Node processing.py
# Alex Lechner
# 28-04-2014
# Version 1.0
# ---------------------------------------------------------------------------


print "running"

# Import arcpy module
import arcpy, time, re, os
import csv
import numpy as np
from arcpy.sa import *

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

print "Starting at " + time.strftime('%d/%m/%y %H:%M:%S')
StartT=time.time()

###################################
# Local variables:
#RootDir = "D:\\_CSRM\\Projects\\AIIRA\\Workspace\\"
RootDir = "D:\\Alex\\_CSRM\\Projects\\AIIRA\\Workspace\\"
InputDir = RootDir + "InputData\\Nodes\\"    #Input directory for nodes
outputDir = RootDir + "Output\\"
#NodeFnameInput= "Elec_Tele_Future"
NodeFnameInput= "Elec_Tele_Current"
#NodeFnameInput= "Roads_Future"
#NodeFnameInput= "RoadsCurrent"
#NodeFnameInput= "access_road200"

NodeFname = NodeFnameInput[0:12]

ClipFile = InputDir + "Extent.shp"
#CellSize = 250 #cellsize in m

rasterTemplate = "D:\\Alex\\_CSRM\\Projects\\AIIRA\\Workspace\\Output\\costSurf.tif" #setup raster template

arcpy.env.overwriteOutput = True

########################################

""" Setup """
os.chdir(RootDir) # Change current working directory for OS operations
arcpy.env.workspace = RootDir # Change current working directory for ArcGIS operations
print(os.getcwd()) #Current directory

#Check if temp directory exists - if not make it
if not os.path.exists(outputDir+"\\Temp"):
    os.makedirs(outputDir+"\\Temp")


########################################
    # node layer
# Process: Clip
ClipInput = InputDir + NodeFnameInput + ".shp"
ClipOutput = outputDir+"Temp\\c"+NodeFname+".shp" 

arcpy.Clip_analysis(ClipInput, ClipFile, ClipOutput, "")

# Process: Feature to Raster
OutputRaster = outputDir+"Temp\\"+NodeFname

tempEnvironment0 = arcpy.env.snapRaster
arcpy.env.snapRaster = rasterTemplate
tempEnvironment1 = arcpy.env.extent
arcpy.env.extent = rasterTemplate
arcpy.PolygonToRaster_conversion(ClipOutput, "FID", OutputRaster, "CELL_CENTER", "NONE", rasterTemplate)
arcpy.env.snapRaster = tempEnvironment0
arcpy.env.extent = tempEnvironment1

# Process: Change Raster value
WeightedRasterFname = outputDir+"Temp\\"+NodeFname+"1" 

WeightedRaster = Raster(OutputRaster)*0+1

#Convert Null values to 0
WeightedRaster = Con(IsNull(WeightedRaster),0, WeightedRaster)

WeightedRaster.save(WeightedRasterFname)        

#Remove decimal places
FinalNode = Raster(outputDir+"Temp\\"+NodeFname+"1")
FinalNode1 = (FinalNode*100)+1

FinalNode1.save(outputDir+"Temp\\"+NodeFname+"I")

#Mask Final feature
maskRasterIn = outputDir+"Temp\\"+NodeFname+"I"
maskRasterOut = outputDir+"Temp\\"+NodeFname+"M"

arcpy.gp.ExtractByMask_sa(maskRasterIn, ClipFile, maskRasterOut)

#Raster mask  - remove areas outside boundary

""" ####### Export to Raster to Tiff""" 
print "Export Node file to Raster to Tiff where 1 = background, 101 = nodes and NoData = 3"

# Local variables:
input_raster = maskRasterOut
output_raster = outputDir+NodeFname + ".tif"

# print output_raster 

# Process: Copy Raster
# (in_raster, out_rasterdataset, config_keyword, background_value, nodata_value, onebit_to_eightbit, colormap_to_RGB, pixel_type
# "8_BIT_SIGNED" , "8_BIT_UNSIGNED" , "32_BIT_UNSIGNED", "32_BIT_FLOAT"
arcpy.CopyRaster_management(input_raster, output_raster, "", "", 0, "NONE", "NONE", "16_BIT_UNSIGNED", "NONE", "NONE") #Note the 0 value converts all 0 pixel values to NoData
#arcpy.CopyRaster_management(input_raster, output_raster, "", "", "", "NONE", "NONE", "16_BIT_UNSIGNED", "NONE", "NONE")

print "Time elapsed:" +str(time.time()- StartT) + " seconds"
print "Finished at:"  +  time.strftime('%d/%m/%y %H:%M:%S')










