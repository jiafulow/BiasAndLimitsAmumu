#!/usr/bin/env python

import sys
import os

from configLimits import *

def makeCards():
    """Produce datacards"""
    
    catList = events.keys()
    #catList = ["amumu_1b1f"]
    
    for cat in catList:
        writeme = []
        separator = "-" * 68
        
        # ______________________________________________________________________
        # Header
        writeme.append("# amumu analysis")
        writeme.append("imax * number of channels")
        writeme.append("jmax * number of processes minus 1")
        writeme.append("kmax * number of nuisance parameters")
        writeme.append(separator)
        rootname = "ws_%s.root" % cat
        writeme.append("shapes {0:<4} {1:<4} {2:<16} {3}:{4}".format(sig, "*", rootname, wsname, prefix+"_"+sig+"_"+cat))
        writeme.append("shapes {0:<4} {1:<4} {2:<16} {3}:{4}".format(bg, "*", rootname, wsname, prefix+"_"+bg+"_"+cat))
        writeme.append("shapes {0:<4} {1:<4} {2:<16} {3}:{4}".format("*", "*", rootname, wsname, "$PROCESS"))
        writeme.append(separator)
        
        # ______________________________________________________________________
        # Counts
        writeme.append("{0:<24} {1:<12}".format("bin", cat))
        writeme.append("{0:<24} {1:<12}".format("observation", -1))
        writeme.append(separator)
        
        s = "{0:<24} ".format("bin")
        for process in processList:
            s += "{0:<12} ".format(cat)
        writeme.append(s)
        
        s = "{0:<24} ".format("process")
        for process in processList:
            s += "{0:<12} ".format(process)
        writeme.append(s)
        
        s = "{0:<24} ".format("process")
        i = 0
        for process in processList:
            s += "{0:>12} ".format(i)
            i += 1
        writeme.append(s)
        
        s = "{0:<24} ".format("rate")
        for process in processList:
            s += "{0:>12} ".format(1.0)
        writeme.append(s)
        writeme.append(separator)
        
        # ______________________________________________________________________
        # Nuisances
        writeme.append("# Uncertainties on yields")
        s = "{0:<16} {1:<8}".format("#lumi_8TeV", "lnN")
        for process in processList:
            s += "{0:>12} ".format(1.026)
        writeme.append(s)
        writeme.append(separator)
        
        writeme.append("# Uncertainties on parameters")
        writeme.append("{0:<36} {1:<10} {2:>6} {3:>6}".format(prefix+"_"+sig+"_mShift_"+cat,"param", 1, 0.03))
        writeme.append("{0:<36} {1:<10} {2:>6} {3:>6}".format(prefix+"_"+sig+"_sigmaShift_"+cat,"param", 1, 0.45))
        writeme.append("{0:<36} {1:<10}".format(prefix+"_"+bg+"_a0_"+cat,"flatParam"))
        writeme.append("{0:<36} {1:<10}".format(prefix+"_"+bg+"_a1_"+cat,"flatParam"))
        writeme.append("{0:<36} {1:<10}".format(prefix+"_"+bg+"_a2_"+cat,"flatParam"))
        writeme.append("{0:<36} {1:<10}".format(prefix+"_"+bg+"_"+cat+"_norm","flatParam"))
        writeme.append("\n")
        
        # ______________________________________________________________________
        # Output
        cardname = "card_%s.txt" % cat
        with open(cardname, "w") as f:
            f.write("\n".join(writeme))
        print "I wrote the datacard: %s" % cardname


# ______________________________________________________________________________
if __name__=="__main__":
    
    # Run
    makeCards()
