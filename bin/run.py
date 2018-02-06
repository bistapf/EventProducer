#python bin/run.py --HELHC --LHE --send -p mg_pp_ee_lo -n 10000 -N 100 --lsf -q 1nh
#python bin/run.py --HELHC --LHE --check --process mg_gg_aa01j_mhcut_5f_HT_0_100
#python bin/run.py --HELHC --LHE --merge
#python bin/run.py --HELHC --LHE --web
#python bin/run.py --HELHC --LHE --remove -p mg_pp_ee_lo
#python bin/run.py --HELHC --LHE --clean -p mg_pp_ee_lo

#python bin/run.py --HELHC --reco --send -p mg_pp_tt_lo --type lhep8 -N 1 --lsf -q 1nh --version helhc_v01
#python bin/run.py --HELHC --reco --send -p p8_pp_Zprime_10TeV_ll -n 10000 --type p8 -N 1 --lsf -q 1nh --version helhc_v01
#python bin/run.py --HELHC --reco --check --version helhc_v01
#python bin/run.py --HELHC --reco --merge --version helhc_v01
#python bin/run.py --HELHC --reco --web --version helhc_v01
#python bin/run.py --HELHC --reco --remove -p mgp8_pp_tt_lo --version helhc_v01
#python bin/run.py --HELHC --reco --clean --version helhc_v01 -p p8_pp_Zprime_10TeV_ttbar

import sys
import EventProducer.common.utils as ut

#__________________________________________________________
if __name__=="__main__":

    import argparse
    parser = argparse.ArgumentParser()

    genTypeGroup = parser.add_mutually_exclusive_group(required = True) # Type of events to generate
    genTypeGroup.add_argument("--reco", action='store_true', help="reco events")
    genTypeGroup.add_argument("--LHE", action='store_true', help="LHE events")

    accTypeGroup = parser.add_mutually_exclusive_group(required = True) # Type of events to generate
    accTypeGroup.add_argument("--FCC", action='store_true', help="100TeV FCC machine")
    accTypeGroup.add_argument("--HELHC", action='store_true', help="27TeV HE-LHC")

    jobTypeGroup = parser.add_mutually_exclusive_group(required = True) # Type of events to generate
    jobTypeGroup.add_argument("--check", action='store_true', help="run the jobchecker")
    jobTypeGroup.add_argument("--merge", action='store_true', help="merge the yaml for all the processes")
    jobTypeGroup.add_argument("--send", action='store_true', help="send the jobs")
    jobTypeGroup.add_argument("--clean", action='store_true', help="clean the dictionnary and eos from bad jobs")
    jobTypeGroup.add_argument("--cleanold", action='store_true', help="clean the yaml from old jobs (more than 72 hours)")
    jobTypeGroup.add_argument("--web", action='store_true', help="print the dictionnary for webpage")
    jobTypeGroup.add_argument("--remove", action='store_true', help="remove a specific process from the dictionary and from eos" )
    jobTypeGroup.add_argument("--sample", action='store_true', help="make the heppy sample list and proc dict" )

    sendjobGroup = parser.add_argument_group('type of jobs to send')
    sendjobGroup.add_argument('--type', type=str, required = '--send' in sys.argv and '--reco'  in sys.argv , help='type of jobs to send', choices = ['lhep8','p8'])
    sendjobGroup.add_argument('-q', '--queue', type=str, default='8nh', help='lxbatch queue (default: 8nh)', choices=['1nh','8nh','1nd','2nd','1nw'])
    sendjobGroup.add_argument('-n','--numEvents', type=int, help='Number of simulation events per job', default=10000)
    sendjobGroup.add_argument('-N','--numJobs', type=int, default = 10, help='Number of jobs to submit')

    args, _ = parser.parse_known_args()

    batchGroup = parser.add_mutually_exclusive_group(required = args.send) # Where to submit jobs
    batchGroup.add_argument("--lsf", action='store_true', help="Submit with LSF")
    batchGroup.add_argument("--condor", action='store_true', help="Submit with condor")

    args, _ = parser.parse_known_args()
    sendOpt = args.type
    

    if args.FCC:
        import EventProducer.config.param_FCC as para
        print 'import FCC config'
    elif args.HELHC:
        import EventProducer.config.param_HELHC as para
        print 'import HE-LHC config'
    else:
        print 'problem, need to specify --FCC or --HELHC'
        sys.exit(3)


    versionGroup = parser.add_argument_group('recontruction version')
    versionGroup.add_argument('--version', type=str, required = '--reco' in sys.argv, help='Version to use', choices = para.fcc_versions)

    decaylist=[]
    for key, value in para.decaylist.iteritems():
        for v in value:
            if v  not in decaylist: decaylist.append(v)
    
    sendjobGroup.add_argument('-d', '--decay', type=str, default='', help='pythia8 decay when needed', choices=decaylist)

    processlist=[]
    if (args.reco and args.type=="p8") or args.check or args.clean or args.merge:
        for key, value in para.pythialist.iteritems():
            processlist.append(key)
    if args.LHE or args.check or args.clean or args.merge or args.reco:
        for key, value in para.gridpacklist.iteritems():
            processlist.append(key)

    parser.add_argument('-p','--process', type=str, help='Name of the process to use to send jobs or for the check', default='', choices=processlist)
    parser.add_argument('--force', action='store_true', help='Force the type of process', default=False)

    args, _ = parser.parse_known_args()
    version = args.version

    indir=None
    yamldir=None
    yamlcheck=None
    fext=None
    statfile=None

    if args.LHE:
        indir=para.lhe_dir
        fext=para.lhe_ext
        yamldir=para.yamldir+'lhe/'
        yamlcheck=para.yamlcheck_lhe
        statfile=para.lhe_stat

    elif args.reco:
        indir='%s%s'%(para.delphes_dir,version)
        fext=para.delphes_ext
        yamldir=para.yamldir+version+'/'
        yamlcheck=para.yamlcheck_reco.replace('VERSION',version)
        statfile=para.delphes_stat.replace('VERSION',version)

        print 'Running reco production system with version %s'%version
    else:
        print 'problem, need to specify --reco or --LHE'
        sys.exit(3)

    if not ut.testeos(para.eostest,para.eostest_size):
        print 'eos seems to have problems, should check, will exit'
        sys.exit(3)
    

    if args.check:
        print 'running the check'
        if args.process!='':
            print 'using a specific process ',args.process
            if args.reco and args.process[0:3]=='mg_': args.process='mgp8_'+args.process[3:]
        import EventProducer.common.checker_yaml as chky
        print args.process
        checker=chky.checker_yaml(indir, para, fext, args.process,  yamldir, yamlcheck)
        checker.check(args.force, statfile)

    elif args.merge:
        print 'running the merger'
        if args.process!='':
            print 'using a specific process ',args.process
            if args.reco and args.process[0:3]=='mg_': args.process='mgp8_'+args.process[3:]
        import EventProducer.common.merger as mgr
        isLHE=args.LHE
        merger = mgr.merger( para, args.process, yamldir, yamlcheck)
        merger.merge(args.force)

    elif args.send:
        print 'sending jobs'        
        if args.lsf:
            print 'send to lsf'
            print 'queue  ', args.queue
        elif args.condor:
            print 'send to condor'
            print 'queue  ', args.queue
 
        if args.LHE:
            print 'preparing to send lhe jobs from madgraph gridpacks for process {}'.format(args.process)
            import EventProducer.bin.send_lhe as slhe
            sendlhe=slhe.send_lhe(args.numJobs,args.numEvents, args.process, args.lsf, args.queue, para)
            sendlhe.send()
        elif args.reco:
            if sendOpt=='lhep8':
                print 'preparing to send FCCSW jobs from lhe'
                import EventProducer.bin.send_lhep8 as slhep8
                sendlhep8=slhep8.send_lhep8(args.numJobs,args.numEvents, args.process, args.lsf, args.queue, para, version, args.decay)
                sendlhep8.send()
            elif sendOpt=='p8':
                print 'preparing to send FCCSW jobs from pythia8 directly'
                import EventProducer.bin.send_p8 as sp8
                sendp8=sp8.send_p8(args.numJobs,args.numEvents, args.process, args.lsf, args.queue, para, version)
                sendp8.send()
        ut.yamlstatus(yamlcheck, args.process, False)

    elif args.web:
        if args.LHE: 
            print 'create web page for LHE'         
            import EventProducer.common.printer as prt
            printdic=prt.printer(yamldir,para.lhe_web, False, True, para)
            printdic.run(yamlcheck)


        elif args.reco:
            print 'create web page for reco version %s'%version
            webpage=para.delphes_web.replace('VERSION',version)
            import EventProducer.common.printer as prt
            printdic=prt.printer(yamldir, webpage, True, False, para, version)
            printdic.run()

    elif args.remove:
        if args.process=='':
            print 'need to specify a process, exit'
            sys.exit(3)
        if args.LHE: 
            print 'remove process %s from eos and database for LHE'%args.process
        elif args.reco: 
            print 'remove process %s from eos and database for reco'%args.process
        import EventProducer.common.removeProcess as rmp
        removeProcess = rmp.removeProcess(args.process, indir, yamldir)
        removeProcess.remove()
        

    elif args.clean:
        print 'clean the dictionnary and eos'
        import EventProducer.common.cleanfailed as clf
        clean=clf.cleanfailed(indir, yamldir, yamlcheck, args.process)
        clean.clean()


    elif args.cleanold:
        print 'clean the dictionnary from old jobs that have not been checked'
        import EventProducer.common.cleanfailed as clf
        clean=clf.cleanfailed(indir, yamldir, yamlcheck, args.process)
        clean.cleanoldjobs()

    elif args.sample:
        print 'make the heppy sample list and procDict'
        import EventProducer.common.makeSampleList as msl
        sample=msl.makeSampleList(para,version)
        sample.makelist()

    else:
        print 'problem, need to specify --check or --send'
        sys.exit(3)
