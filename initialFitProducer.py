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

vladimir = False

donotdelete = []


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
    #tlatex.DrawLatex(0.64, 0.76, "#color[600]{N_{s} = %.2f +/- %.2f}" % (ws.var("nsig").getVal(), ws.var("nsig").getError()))
    tlatex.DrawLatex(0.64, 0.76, "#color[600]{Signif = %.2f#sigma}" % (ws.var("signif").getVal()))
    
    argset = ROOT.RooArgSet(ws.var("x"))
    s0 = ws.pdf("gauss").createIntegral(argset).getVal()
    s1 = ws.pdf("gauss").createIntegral(argset,RooFit.Range("xsignal")).getVal()
    #s2 = ws.pdf("gauss").createIntegral(argset,RooFit.NormSet(argset),RooFit.Range("xsignal")).getVal()
    b0 = ws.pdf("pol").createIntegral(argset).getVal()
    b1 = ws.pdf("pol").createIntegral(argset,RooFit.Range("xsignal")).getVal()
    #b2 = ws.pdf("pol").createIntegral(argset,RooFit.NormSet(argset),RooFit.Range("xsignal")).getVal()
    tlatex.DrawLatex(0.64, 0.72, "#color[600]{N_{s} [26,32] = %.2f +/- %.2f}" % (ws.var("nsig").getVal()*s1/s0, ws.var("nsig").getError()*s1/s0))
    tlatex.DrawLatex(0.64, 0.68, "#color[600]{N_{b} [26,32] = %.2f +/- %.2f}" % (ws.var("nbkg").getVal()*b1/b0, ws.var("nbkg").getError()*b1/b0))


# ______________________________________________________________________________
def doInitialFits():
    """Do initial fits"""
    
    catList = events.keys()
    #catList = ["amumu_1b1f"]
    
    for cat in catList:
        ttree = getTTree(events[cat], tname)
        
        # ______________________________________________________________________
        # Init a workspace
        ws = ROOT.RooWorkspace(wsname, wsname)
    
        x = ws.factory("%s[%s,%s,%s]" % (xname, str(x0), str(xmin), str(xmax)))
        x.SetTitle(xtitle)
        
        nbinsx = float(xmax - xmin)/binw
        x.setRange(xmin, xmax)
        x.setRange("xsignal", 26, 32)
        x.setBins(int(nbinsx))
        #x.setBins(50000, "cache")
        #wgt = ws.factory("__WEIGHT__[0.,1000.]")
        
        #ws.Print()
        
        # ______________________________________________________________________
        # Get the data
        data = getData(ttree, x, xcuts)
        getattr(ws,'import')(data)
        
        # ______________________________________________________________________
        # Make the fit
        fitBuilder = FitBuilder(ws, cat)
        
        frame = x.frame()
        frame.SetTitle("")
        data.plotOn(frame)
        
        model = fitBuilder.Build("Gauss+Pol")
        nsig = ws.var("nsig")
        nsig.setVal(0.); nsig.setConstant(True)
        #r0 = model.fitTo(data, RooFit.Save(True), RooFit.Extended(True)); r0.Print()
        r0 = model.fitTo(data, RooFit.Save(True), RooFit.Extended(True), RooFit.Minimizer("Minuit2","Migrad"), RooFit.Hesse(True), RooFit.Minos(True), RooFit.PrintLevel(-1)); r0.Print()
        nsig.setConstant(False)
        #r = model.fitTo(data, RooFit.Save(True), RooFit.Extended(True)); r.Print()
        r = model.fitTo(data, RooFit.Save(True), RooFit.Extended(True), RooFit.Minimizer("Minuit2","Migrad"), RooFit.Hesse(True), RooFit.Minos(True), RooFit.PrintLevel(-1)); r.Print()
        
        signif = sqrt(2.0*abs(r.minNll() - r0.minNll()))
        ws.factory("signif[%s]" % str(signif))
        
        model.plotOn(frame, RooFit.Components("gauss"), RooFit.LineStyle(2), RooFit.Invisible())
        model.plotOn(frame, RooFit.Components("pol"), RooFit.LineStyle(2))
        model.plotOn(frame)
        #model.plotOn(frame, RooFit.Components("pol"), RooFit.LineStyle(2), RooFit.Normalization(1.0,ROOT.RooAbsReal.RelativeExpected))
        #model.plotOn(frame, RooFit.Components(ROOT.RooArgSet(ws.pdf("pol"),ws.pdf("gauss"))), RooFit.LineStyle(3), RooFit.Normalization(1.0,ROOT.RooAbsReal.RelativeExpected))
        intsig = ws.pdf("gauss").createIntegral(ROOT.RooArgSet(x)).getVal()
        intbkg = ws.pdf("pol").createIntegral(ROOT.RooArgSet(x)).getVal()
        nsig_func = ws.factory("nsig_func[0]")
        nsig_func.setVal(ws.var("nsig").getVal()/intsig)
        nsig_func.setError(ws.var("nsig").getError()/intsig)
        nbkg_func = ws.factory("nbkg_func[0]")
        nbkg_func.setVal(ws.var("nbkg").getVal()/intbkg)
        nbkg_func.setError(ws.var("nbkg").getError()/intbkg)
        print "intsig,intbkg,nsig_func,nbkg_func =", intsig, intbkg, nsig_func.getVal(), "+/-", nsig_func.getError(), nbkg_func.getVal(), "+/-", nbkg_func.getError()
        frame.SetMaximum(frame.GetMaximum()*1.3)
        print "ymax =", frame.GetMaximum()
        gPad.SetLeftMargin(0.15); frame.GetYaxis().SetTitleOffset(1.2); frame.Draw()
        addText(ws)
        
        # ______________________________________________________________________
        # Print
        gPad.Print("fit_%s.png" % cat)
        gPad.Print("fit_%s.pdf" % cat)
        
        # ______________________________________________________________________
        # Vladimir's fit (NOT WORKING)
        if vladimir:
            def get_histogram(frame, cname, hname):
                curve = frame.getCurve(cname)
                #h = curve.GetHistogram().Clone(hname)
                h = ROOT.TH1F(hname, frame.GetTitle(), frame.GetNbinsX(), frame.GetXaxis().GetXmin(), frame.GetXaxis().GetXmax())
                n = curve.GetN()
                print n
                x = curve.GetX()
                y = curve.GetY()
                for i in xrange(n):
                    for j in xrange(int(y[i])):
                        h.Fill(x[i])
                return h

            def write_histos(cat, histos):
                fname = "histos_%s.root" % cat
                tfile1 = ROOT.TFile.Open(fname, "RECREATE")
                for h in histos:
                    h.SetDirectory(tfile1)
                tfile1.Write()
                tfile1.Close()

            h_model = get_histogram(frame, "model_Norm[x]", "h_model")
            h_sig = get_histogram(frame, "model_Norm[x]_Comp[gauss]", "h_sig")
            h_bkg = get_histogram(frame, "model_Norm[x]_Comp[pol]", "h_bkg")
            write_histos(cat, [h_model, h_sig, h_bkg])

        # ______________________________________________________________________
        # Fix the parameter names
        nameFixer = NameFixer(ws, cat, prefix)
        nameFixer.Fix(sig, bg)
        
        # ______________________________________________________________________
        # Output
        donotdelete.append(frame)
        #donotdelete.append(model)
        #donotdelete.append(data)
        
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
    c1 = TCanvas()
    doInitialFits()

    # Sanity check
    check()
