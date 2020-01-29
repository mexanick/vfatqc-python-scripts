#!/bin/env python
r"""
Dac Scan
========

Performs a VFAT3 DAC scan on all unmasked optohybrids. Measures the correspondence between DAC units 
and physical values (in fC, uA, or V depending on the register of interest).

``dacScanV3.py``
================

Synopsis
--------

**run_scans.py** **dacScanV3** [-**h**] [--**dacSelect** *DACSELECT*] [-**e**] shelf slot ohMask

Mandatory arguments
-------------------

.. program:: run_Scans.py dacScanV3

Positional arguments
--------------------

.. option:: shelf

    uTCA crate shelf number

.. option:: slot
   
    AMC slot number in the uTCA crate

.. option:: ohMask

    optohybrid mask to apply, a 1 in the n^{th} bit indicates the n^{th} OH should be considered

Optional arguments
------------------

.. option:: -h, --help

    show the help message and exit

.. option:: --dacSelect <DACSELECT>

    DAC Selection, see `The VFAT3 Manual <https://espace.cern.ch/cms-project-GEMElectronics/VFAT3/Forms/AllItems.aspx>`_

.. option:: -e, --extRefADC

    Use the externally referenced ADC on the VFAT3

Environment
-----------

The following `$SHELL` variables should be defined beforehand:

.. glossary::

:envvar: `BUILD_HOME`
    the location of your ``vfatqc-python-scripts`` directory
:envvar: `DATA_PATH`
    the location of input data

Then execute:

`source $BUILD_HOME/vfatqc-python-scripts/setup/paths.sh`
"""
from gempython.tools.hw_constants import maxVfat3DACSize

import os

if __name__ == '__main__':
    """
    Script to perform DAC scans with VFAT3
    By: Brian Dorney (brian.l.dorney@cern.ch)
    """

    # create the parser
    import argparse
    parser = argparse.ArgumentParser(description="Scans a given DAC on a VFAT3 against the chip's ADC.  Either the internally or externally referenced ADC can be used.  Scans all VFATs on a given link simultaneously")

    # Positional arguments
    from reg_utils.reg_interface.common.reg_xml_parser import parseInt
    parser.add_argument("shelf", type=int, help="uTCA shelf to access")
    parser.add_argument("slot", type=int,help="slot in the uTCA of the AMC you are connceting too")
    parser.add_argument("ohMask", type=parseInt, help="ohMask to apply, a 1 in the n^th bit indicates the n^th OH should be considered", metavar="ohMask")
    
    # Optional arguments
    parser.add_argument("-d","--debug", action="store_true", dest="debug",
            help = "Print additional debugging information")
    parser.add_argument("--dacSelect", type=int, dest="dacSelect",
            help = "DAC Selection", default=None)
    parser.add_argument("-e","--extRefADC", action="store_true", dest="extRefADC",
            help = "Use the externally referenced ADC on the VFAT3.")
    parser.add_argument("-f","--filename",type=str,dest="filename",default="dacScanV3.root",
            help = "Specify output filename to store data in.")
    parser.add_argument("--series", action="store_true", dest="series",
            help = "Scan nonzero links in ohMask in series (successive RPC calls) instead of in parallel (one RPC call)")
    parser.add_argument("--stepSize", type=int, dest="stepSize",default=1, 
                  help="Supply a step size for the scan")
    parser.add_argument("-v","--vfatmask",type=parseInt,dest="vfatmask",default=None,
            help="VFATs to be masked in scan & analysis applications (e.g. 0xFFFFF masks all VFATs)")
    args = parser.parse_args()

    from gempython.utils.gemlogger import printRed
    if ((args.dacSelect not in maxVfat3DACSize.keys()) and (args.dacSelect is not None)):
        printRed("Input DAC selection {0} not understood".format(args.dacSelect))
        printRed("possible options include:")
        from gempython.vfatqc.utils.qcutilities import printDACOptions
        printDACOptions()
        exit(os.EX_USAGE)

    # Open rpc connection to hw
    from gempython.vfatqc.utils.qcutilities import getCardName, inputOptionsValid
    cardName = getCardName(args.shelf,args.slot)
    from gempython.tools.vfat_user_functions_xhal import *
    vfatBoard = HwVFAT(cardName, 0, args.debug) # Assign link 0; we will update later
    print 'opened connection'
    amcBoard = vfatBoard.parentOH.parentAMC
    if amcBoard.fwVersion < 3:
        printRed("DAC Scan of v2b electronics is not supported, exiting!!!")
        exit(os.EX_USAGE)
    
    # Check options
    if not inputOptionsValid(args, amcBoard.fwVersion):
        exit(os.EX_USAGE)
        pass
    
    # Make output files
    import ROOT as r
    outF = r.TFile(args.filename,"RECREATE")
    from gempython.vfatqc.utils.scanUtils import dacScanAllLinks, dacScanSingleLink 
    from gempython.vfatqc.utils.treeStructure import gemDacCalTreeStructure
    calTree = gemDacCalTreeStructure(
                    name="dacScanTree",
                    nameX="dummy", # temporary name, will be over-ridden
                    nameY=("ADC1" if args.extRefADC else "ADC0"),
                    dacSelect=-1, #temporary value, will be over-ridden 
                    description="GEM DAC Calibration of VFAT3 DAC"
            )

    if args.dacSelect is None: # No DAC selected; scan them all
        for dacSelect in maxVfat3DACSize.keys():
            args.dacSelect = dacSelect
            if args.series:
                for ohN in range(0, amcBoard.nOHs):
                    if( not ((args.ohMask >> ohN) & 0x1)):
                        continue

                    # update the OH in question
                    vfatBoard.parentOH.link = ohN

                    dacScanSingleLink(args, calTree, vfatBoard)
                    pass
                pass
            else:
                dacScanAllLinks(args, calTree, vfatBoard)
    else: # Specific DAC Requested; scan only this DAC
        if args.series:
            for ohN in range(0, amcBoard.nOHs):
                if( not ((args.ohMask >> ohN) & 0x1)):
                    continue

                # update the OH in question
                vfatBoard.parentOH.link = ohN

                dacScanSingleLink(args, calTree, vfatBoard)
                pass
            pass
        else:
            dacScanAllLinks(args, calTree, vfatBoard)

    outF.cd()
    calTree.autoSave("SaveSelf")
    calTree.write()
    outF.Close()

    print("All DAC Scans Completed. Goodbye")
