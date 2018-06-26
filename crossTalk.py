#!/bin/env python

def main():
    from gempython.tools.xdaq.amc13manager import AMC13Manager
    from gempython.vfatqc.qcoptions import parser

    parser.add_option("--filename", type="string", dest="filename", default="crossTalke",
                      help="Specify Output Filename without extension", metavar="filename")

    parser.add_option("--delay", type="int", dest="delay", default=50,
                      help="Delay between L1A and CalPulse", metavar="delay")

    parser.add_option("--prescale", type="int", dest="prescale", default=1,
                      help="CalPulse prescale", metavar="prescale")
    (options, args) = parser.parse_args()

    if options.debug:
        verbosity = 5
        uhal.setLogLevelTo(uhal.LogLevel.INFO)
    else:
        verbosity = 1
        uhal.setLogLevelTo(uhal.LogLevel.ERROR)

    amc13base  = "gem.shelf%02d.amc13"%(options.shelf)
    
    crossTalkScan(amc13base, verbosity, options.delay, options.prescale, options.filename)


def crossTalkScan(amc13base, verbosity, delay, prescale, filename):
    # Connect to amc13
    m_amc13manager = AMC13manager()
    m_amc13manager.connect(amc13base, verbosity)
    #setup localL1A
    m_amc13manager.configureTrigger(True,0)
    #setup calibration pulse BGO
    m_amc13manager.configureCalPulse(delay, prescale)


if __name__ == '__main__':
    """
    Script to take data for cross talk studies
    By: Mykhailo Dalchenko (mykhailo.dalchenko@cern.ch)
    """
    main()

