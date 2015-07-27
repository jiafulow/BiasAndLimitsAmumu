#!/usr/bin/env python

# class for multi-layered nested dictionaries, pretty cool
class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

events = {
"amumu_1b1f": "amumuFile_MuMu2012ABCD_sasha_17.root",
"amumu_1b1c": "amumuFile_MuMu2012ABCD_sasha_28.root",
}

tname = "amumuTree_DATA"

xname = "x"
xtitle = "M(#mu#mu) [GeV]"
xcuts = "x>0"

x0 = 28
xmin = 12
xmax = 70
binw = 2

wsname = "ws_8TeV"

prefix = "CMS_amumu"

processList = ["sig", "bg"]

assert(len(processList)>=2)
sig = processList[0]
bg = processList[1]
