#!/usr/bin/env python

import sys
import os
from math import sqrt

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
sys.argv.append( '-b-' )
import ROOT
from ROOT import gROOT, gStyle, gPad, RooFit, TCanvas, TLatex
gROOT.SetBatch(True)
sys.argv.remove( '-b-' )

from configLimits import *
from fitBuilder import *

# ______________________________________________________________________________
tlatex = TLatex()
tlatex.SetNDC()
tlatex.SetTextFont(42)
tlatex.SetTextSize(0.03)


# ______________________________________________________________________________
def getTTree(fname, tname):
    """Open a .root file, retrieve a TTree"""
    
    if not fname.endswith(".root"):
        raise RuntimeError("Input not a .root file", fname)
    
    tfile = ROOT.TFile.Open(fname)
    if not tfile:
        raise RuntimeError("Cannot open file", fname)
        
    ttree = tfile.Get(tname)
    if not ttree:
        raise RuntimeError("Cannot get tree", tname)
    return ttree

def getData(ttree, x, cuts="1", weight="__WEIGHT__"):
    """Import a TTree as a RooDataSet (unbinned)"""
    
    ds = ROOT.RooDataSet("data_obs", "data_obs", ttree, ROOT.RooArgSet(x), cuts, weight)
    return ds

def getWorkspace(fname, wsname):
    """Open a .root file, retrieve a RooWorkspace"""
    
    if not fname.endswith(".root"):
        raise RuntimeError("Input not a .root file", fname)
    
    tfile = ROOT.TFile.Open(fname)
    if not tfile:
        raise RuntimeError("Cannot open file", fname)
        
    ws = tfile.Get(wsname)
    if not ws:
        raise RuntimeError("Cannot get workspace", wsname)
    return ws

def addText(ws):
    tlatex.DrawLatex(0.18, 0.84, "Nevts [12,70]: %.0f" % (ws.data("data_obs").sumEntries("12<=x && x<=70")))
    tlatex.DrawLatex(0.18, 0.80, "Nevts [26,32]: %.0f" % (ws.data("data_obs").sumEntries("26<=x && x<=32")))
    
    tlatex.DrawLatex(0.64, 0.88, "#color[600]{Signal fit}")
    tlatex.DrawLatex(0.64, 0.84, "#color[600]{#mu = %.2f +/- %.2f}" % (ws.var("mean").getVal(), ws.var("mean").getError()))
    tlatex.DrawLatex(0.64, 0.80, "#color[600]{#sigma = %.2f +/- %.2f}" % (ws.var("sigma").getVal(), ws.var("sigma").getError()))
    tlatex.DrawLatex(0.64, 0.76, "#color[600]{N_{s} = %.2f +/- %.2f}" % (ws.var("nsig").getVal(), ws.var("nsig").getError()))
    tlatex.DrawLatex(0.64, 0.72, "#color[600]{Signif = %.2f#sigma (stat only)}" % (ws.var("signif").getVal()))


# ______________________________________________________________________________
def doInitialFits():
    """Do initial fits"""
    
    catList = events.keys()
    #catList = ["amumu_1b1f"]
    
    c1 = TCanvas()
    
    for cat in catList:
        ttree = getTTree(events[cat], tname)
        
        # ______________________________________________________________________
        # Init a workspace
        ws = ROOT.RooWorkspace(wsname, wsname)
    
        x = ws.factory("%s[%s,%s,%s]" % (xname, str(x0), str(xmin), str(xmax)))
        x.SetTitle(xtitle)
        
        nbinsx = float(xmax - xmin)/binw
        x.setRange(xmin, xmax)
        x.setBins(int(nbinsx))
        #x.setBins(50000, "cache")
        #wgt = ws.factory("__WEIGHT__[0.,1000.]")
        
        #ws.Print()
        
        # ______________________________________________________________________
        # Get the data
        ds = getData(ttree, x, xcuts)
        getattr(ws,'import')(ds)
        
        # ______________________________________________________________________
        # Make the fit
        fitBuilder = FitBuilder(ws, cat)
        
        frame = x.frame()
        frame.SetTitle("")
        ds.plotOn(frame)
        
        model = fitBuilder.Build("Gauss+Pol")
        nsig = ws.var("nsig")
        nsig.setVal(0.); nsig.setConstant(True)
        #r0 = model.fitTo(ds, RooFit.Save(True), RooFit.Extended(True)); r0.Print()
        r0 = model.fitTo(ds, RooFit.Save(True), RooFit.Extended(True), RooFit.Minimizer("Minuit2","Migrad"), RooFit.Hesse(True), RooFit.Minos(True), RooFit.PrintLevel(-1)); r0.Print()
        nsig.setConstant(False)
        #r = model.fitTo(ds, RooFit.Save(True), RooFit.Extended(True)); r.Print()
        r = model.fitTo(ds, RooFit.Save(True), RooFit.Extended(True), RooFit.Minimizer("Minuit2","Migrad"), RooFit.Hesse(True), RooFit.Minos(True), RooFit.PrintLevel(-1)); r.Print()
        
        signif = sqrt(2.0*abs(r.minNll() - r0.minNll()))
        ws.factory("signif[%s]" % str(signif))
        
        model.plotOn(frame)
        gPad.SetLeftMargin(0.15); frame.GetYaxis().SetTitleOffset(1.2); frame.Draw()
        addText(ws)
        
        # ______________________________________________________________________
        # Print
        gPad.Print("fit_%s.png" % cat)
        gPad.Print("fit_%s.pdf" % cat)
        
        # ______________________________________________________________________
        # Fix the parameter names
        nameFixer = NameFixer(ws, cat, prefix)
        nameFixer.Fix(sig, bg)
        
        # ______________________________________________________________________
        # Output
        rootname = "ws_%s.root" % cat
        ws.writeToFile(rootname)
        print "I wrote the workspace: %s" % rootname


def check():
    """Do sanity check"""
    
    catList = events.keys()
    #catList = ["amumu_1b1f"]
    
    for cat in catList:
        rootname = "ws_%s.root" % cat
        
        ws = getWorkspace(rootname, wsname)
        
        ws.Print()
        ws.var(prefix+"_"+sig+"_"+cat+"_norm").Print()
        ws.var(prefix+"_"+sig+"_mShift_"+cat).Print()
        ws.var(prefix+"_"+sig+"_sigmaShift_"+cat).Print()
        ws.var(prefix+"_"+bg+"_"+cat+"_norm").Print()
        ws.var(prefix+"_"+bg+"_a0_"+cat).Print()
        ws.var(prefix+"_"+bg+"_a1_"+cat).Print()
        ws.var(prefix+"_"+bg+"_a2_"+cat).Print()
        
        print "mean: {0:.3f}, frac err: {1:.3f}".format(ws.var("mean").getVal(), ws.var("mean").getError()/ws.var("mean").getVal())
        print "sigma: {0:.3f}, frac err: {1:.3f}".format(ws.var("sigma").getVal(), ws.var("sigma").getError()/ws.var("sigma").getVal())
        print "signif: {0:.4f}".format(ws.var("signif").getVal())


# ______________________________________________________________________________
if __name__=="__main__":
    
    # Init
    gROOT.LoadMacro("tdrstyle.C")
    gROOT.ProcessLine("setTDRStyle()")
    gStyle.SetLabelSize(0.04, "Z")
    
    # Run
    doInitialFits()

    # Sanity check
    check()
