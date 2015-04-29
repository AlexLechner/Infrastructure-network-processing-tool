# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Least-code path cost-surface processing tool
# Cost-surface processing.py
# Alex Lechner
# 28-04-2014
# Version 1.0
# ---------------------------------------------------------------------------


print "running"
import time
print "Starting at " + time.strftime('%d/%m/%y %H:%M:%S')
StartT=time.time()

# Import arcpy module
import arcpy,  re, os
import csv
import numpy as np
from arcpy.sa import *

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

print " "
print "######################################################"
print "      Least-code path cost-surface processing tool"
print "######################################################"
print " "

###################################
# Local variables:
#RootDir = "D:\\_CSRM\\Projects\\AIIRA\\Workspace\\"
RootDir = "D:\\Alex\\_CSRM\\Projects\\AIIRA\\Workspace\\"
InputShpDir = RootDir + "InputData\\Factors\\"
InputDir = RootDir + "InputData\\"
outputDir = RootDir + "Output\\"
CostSurfaceFname = "costSurf"

ClipFile = InputDir + "Extent.shp"
CellSize = 100 #cellsize in m
CellSizeTopo ="100"

InputFilesAndWeightings = InputDir+"FilesAndWeightings.csv"

#Topography
InputContours= InputDir+ "Contours.shp ELEVASI Contour"
OutputRasterTopo = "topo"

rasterTemplate = outputDir+OutputRasterTopo

arcpy.env.overwriteOutput = True

#Rerun analaysis
rerunClipCheck = 1
retunTopoCheck = 1

########################################

""" Setup """
os.chdir(RootDir) # Change current working directory for OS operations
arcpy.env.workspace = RootDir # Change current working directory for ArcGIS operations
print(os.getcwd()) #Current directory

#Check if temp directory exists - if not make it
if not os.path.exists(outputDir+"\\Temp"):
    os.makedirs(outputDir+"\\Temp")


########################################
# RasterToTopo
# Local variables
# Process: Topo to Raster
if retunTopoCheck ==1:
    print ("====Running topo with cell size %s and input file -> %s" % (CellSize, InputContours))
    OutputRasterTopo1 = outputDir+ "Temp\\" + OutputRasterTopo+"1"

    arcpy.gp.TopoToRaster_sa(InputContours, OutputRasterTopo1, CellSizeTopo, ClipFile, "20", "", "", "ENFORCE", "CONTOUR", "20", "", "1", "0", "1")

    # Process: Slope
    inputTopo = OutputRasterTopo1
    outSlope = outputDir+ "Temp\\" + OutputRasterTopo+"2"
    arcpy.gp.Slope_sa(inputTopo, outSlope, "PERCENT_RISE", "1")

    # Process: Reclassify
    OutputRasterTopo2 = outputDir+OutputRasterTopo
    arcpy.gp.Reclassify_sa(outSlope, "Value", "0 3 1;3 25 2;25 90 5", OutputRasterTopo2, "DATA")
    #arcpy.gp.Reclassify_sa(outSlope, "Value", "0 3 100;3 25 10", OutputRasterTopo2, "DATA")

    print ("====Output topo-> %s" % (OutputRasterTopo1))


########################################
#Process and weight files

print ("====Process and weight files")

orignalCSV =np.genfromtxt(InputFilesAndWeightings,delimiter=',', dtype=None)

#listOfFiles = orignalCSV [1:3,0] # arrays are subsetted y,x
listOfFiles = orignalCSV [1:,0]


count=1
previouscurrentfilelocation =""

for currentfile in listOfFiles:
    currentfilelocation = InputShpDir+currentfile
    currentWeight = orignalCSV[count,1]
    
    getfilename = re.search('\\\\(.+?).shp', currentfile) #
    CurrentFilenameOnly = getfilename.group(1)

    print "currentfilelocation is: %s ,currentWeight is %s" % (currentfilelocation, currentWeight)
    
    if currentfilelocation != previouscurrentfilelocation:
        ####################### only reanalyse the data if the next factor uses a different file
        
        # Process: Clip
        ClipInput = currentfilelocation

        ClipOutput = outputDir+"Temp\\clip"+CurrentFilenameOnly+".shp"

        if rerunClipCheck == 1: #This 
            arcpy.Clip_analysis(ClipInput, ClipFile, ClipOutput, "")

        # Process: Feature to Raster
        OutputRaster = outputDir+"Temp\\"+CurrentFilenameOnly[0:12] 
        
        tempEnvironment0 = arcpy.env.snapRaster
        arcpy.env.snapRaster = rasterTemplate
        tempEnvironment1 = arcpy.env.extent
        arcpy.env.extent = rasterTemplate
        #arcpy.PolygonToRaster_conversion(ClipOutput, "FID", OutputRaster, "CELL_CENTER", "NONE", rasterTemplate)
        arcpy.PolygonToRaster_conversion(ClipOutput, "FID", OutputRaster, "MAXIMUM_COMBINED_AREA", "NONE", rasterTemplate)
        #arcpy.PolygonToRaster_conversion(ClipOutput, "FID", OutputRaster, "MAXIMUM_AREA", "NONE", rasterTemplate)
        arcpy.env.snapRaster = tempEnvironment0
        arcpy.env.extent = tempEnvironment1

        # Process: Change Raster value
        WeightedRasterFname = outputDir+"Temp\\"+CurrentFilenameOnly[0:12]+"1" 
        
        WeightedRaster = Raster(OutputRaster)*0+float(currentWeight)

        #Convert Null values to 0
        WeightedRaster = Con(IsNull(WeightedRaster),0, WeightedRaster)
        
        WeightedRaster.save(WeightedRasterFname)        

    previouscurrentfilelocation = currentfilelocation #Keep track of which files have been altered

    if count != 1:
        print "Modifying cost surface"
        CostSurface = Raster(outputDir+"Temp\\"+CostSurfaceFname+str(count-1))
        newCostSurface = Plus(CostSurface,WeightedRaster)
        newCostSurface.save(outputDir+"Temp\\"+CostSurfaceFname+str(count))
    else:
        print "Creating cost surface"
        WeightedRaster.save(outputDir+"Temp\\"+CostSurfaceFname+"1")
    
    count= count+1

    ###End loop

print "====Finished processing factors. final cost surface-> %s" % (outputDir+"Temp\\"+CostSurfaceFname+str(count))
#Process final cost surface and add topo surface

#open finalcostsurface and raster
FinalCostSurface = Raster(outputDir+"Temp\\"+CostSurfaceFname+str(count-1))
FinalCostSurface.save(outputDir+CostSurfaceFname+str(count))

TopoLayer = Raster(OutputRasterTopo2)

#Normalise - make all values positive - convert to cost weighting
FinalCostSurfaceMINresult = arcpy.GetRasterProperties_management(outputDir+"Temp\\"+CostSurfaceFname+str(count-1),"MINIMUM")
FinalCostSurfaceMIN = FinalCostSurfaceMINresult.getOutput(0) #Get minimum values

FinalCostSurfaceMAXresult = arcpy.GetRasterProperties_management(outputDir+"Temp\\"+CostSurfaceFname+str(count-1),"MAXIMUM")
FinalCostSurfaceMAX = FinalCostSurfaceMAXresult.getOutput(0) #Get maximum values

print "the maximum value is: %s ,the minimum values is %s" % (FinalCostSurfaceMAX , FinalCostSurfaceMIN)

MinPixel = abs(float(FinalCostSurfaceMIN))
MaxPixel= float(FinalCostSurfaceMAX)
maxminPixel=max([MinPixel,MaxPixel])
rangePixel = MaxPixel - MinPixel
CellSizeINT = int(CellSize)

#rescale cost surface
CostSurfaceRescaled = ((FinalCostSurface * -1)+ MaxPixel)*CellSize
CostSurfaceRescaled.save(outputDir+"Temp\\"+"CSRescale")

#Combine cost surface with topographic layer
TopographicInterval = rangePixel/5*CellSize
FinalCostSurface = CostSurfaceRescaled + TopoLayer * TopographicInterval

FinalCostSurface.save(outputDir+"Temp\\"+CostSurfaceFname+"INT")

#Mask Final feature
maskRasterIn = outputDir+"Temp\\"+CostSurfaceFname+"INT"
maskRasterOut = outputDir+"Temp\\"+CostSurfaceFname+"MSK"

arcpy.gp.ExtractByMask_sa(maskRasterIn, ClipFile, maskRasterOut)

#Raster mask  - remove areas outside boundary

""" ####### Export to Raster to Tiff""" 
print "Export resistance file to Raster to Tiff"

# Local variables:
input_raster = maskRasterOut
output_raster = outputDir+CostSurfaceFname + ".tif"

# print output_raster 

# Process: Copy Raster
# (in_raster, out_rasterdataset, config_keyword, background_value, nodata_value, onebit_to_eightbit, colormap_to_RGB, pixel_type
# "8_BIT_SIGNED" , "8_BIT_UNSIGNED" , "32_BIT_UNSIGNED", "32_BIT_FLOAT"
arcpy.CopyRaster_management(input_raster, output_raster, "", "", 0, "NONE", "NONE", "16_BIT_UNSIGNED", "NONE", "NONE") #Note the 0 value converts all 0 pixel values to NoData
#arcpy.CopyRaster_management(input_raster, output_raster, "", "", "", "NONE", "NONE", "16_BIT_UNSIGNED", "NONE", "NONE")
print ("====Output cost surface-> %s" % (output_raster))

print "Time elapsed:" +str(time.time()- StartT) + " seconds"
print "Finished at:"  +  time.strftime('%d/%m/%y %H:%M:%S')










