#define rand	pan_rand
#define pthread_equal(a,b)	((a)==(b))
#if defined(HAS_CODE) && defined(VERBOSE)
	#ifdef BFS_PAR
		bfs_printf("Pr: %d Tr: %d\n", II, t->forw);
	#else
		cpu_printf("Pr: %d Tr: %d\n", II, t->forw);
	#endif
#endif
	switch (t->forw) {
	default: Uerror("bad forward move");
	case 0:	/* if without executable clauses */
		continue;
	case 1: /* generic 'goto' or 'skip' */
		IfNotBlocked
		_m = 3; goto P999;
	case 2: /* generic 'else' */
		IfNotBlocked
		if (trpt->o_pm&1) continue;
		_m = 3; goto P999;

		 /* CLAIM invariant_balance */
	case 3: // STATE 1 - _spin_nvr.tmp:19 - [(!((balance>=0)))] (6:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[3][1] = 1;
		if (!( !((now.balance>=0))))
			continue;
		/* merge: assert(!(!((balance>=0))))(0, 2, 6) */
		reached[3][2] = 1;
		spin_assert( !( !((now.balance>=0))), " !( !((balance>=0)))", II, tt, t);
		/* merge: .(goto)(0, 7, 6) */
		reached[3][7] = 1;
		;
		_m = 3; goto P999; /* 2 */
	case 4: // STATE 10 - _spin_nvr.tmp:24 - [-end-] (0:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported10 = 0;
			if (verbose && !reported10)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported10 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported10 = 0;
			if (verbose && !reported10)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported10 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[3][10] = 1;
		if (!delproc(1, II)) continue;
		_m = 3; goto P999; /* 0 */

		 /* CLAIM liveness_progress */
	case 5: // STATE 1 - _spin_nvr.tmp:13 - [(!((state==1)))] (0:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[2][1] = 1;
		if (!( !((((int)now.state)==1))))
			continue;
		_m = 3; goto P999; /* 0 */
	case 6: // STATE 6 - _spin_nvr.tmp:15 - [-end-] (0:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported6 = 0;
			if (verbose && !reported6)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported6 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported6 = 0;
			if (verbose && !reported6)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported6 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[2][6] = 1;
		if (!delproc(1, II)) continue;
		_m = 3; goto P999; /* 0 */

		 /* CLAIM safety_no_overflow */
	case 7: // STATE 1 - _spin_nvr.tmp:3 - [(!(((balance>=0)&&(balance<=1000000))))] (6:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported1 = 0;
			if (verbose && !reported1)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported1 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[1][1] = 1;
		if (!( !(((now.balance>=0)&&(now.balance<=1000000)))))
			continue;
		/* merge: assert(!(!(((balance>=0)&&(balance<=1000000)))))(0, 2, 6) */
		reached[1][2] = 1;
		spin_assert( !( !(((now.balance>=0)&&(now.balance<=1000000)))), " !( !(((balance>=0)&&(balance<=1000000))))", II, tt, t);
		/* merge: .(goto)(0, 7, 6) */
		reached[1][7] = 1;
		;
		_m = 3; goto P999; /* 2 */
	case 8: // STATE 10 - _spin_nvr.tmp:8 - [-end-] (0:0:0 - 1)
		
#if defined(VERI) && !defined(NP)
#if NCLAIMS>1
		{	static int reported10 = 0;
			if (verbose && !reported10)
			{	int nn = (int) ((Pclaim *)pptr(0))->_n;
				printf("depth %ld: Claim %s (%d), state %d (line %d)\n",
					depth, procname[spin_c_typ[nn]], nn, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported10 = 1;
				fflush(stdout);
		}	}
#else
		{	static int reported10 = 0;
			if (verbose && !reported10)
			{	printf("depth %d: Claim, state %d (line %d)\n",
					(int) depth, (int) ((Pclaim *)pptr(0))->_p, src_claim[ (int) ((Pclaim *)pptr(0))->_p ]);
				reported10 = 1;
				fflush(stdout);
		}	}
#endif
#endif
		reached[1][10] = 1;
		if (!delproc(1, II)) continue;
		_m = 3; goto P999; /* 0 */

		 /* PROC Program */
	case 9: // STATE 1 - /home/slade/defi_guardian/translated_output.pml:18 - [printf('Validating Rust State Machine...\\n')] (0:23:1 - 1)
		IfNotBlocked
		reached[0][1] = 1;
		Printf("Validating Rust State Machine...\n");
		/* merge: state = 1(23, 2, 23) */
		reached[0][2] = 1;
		(trpt+1)->bup.oval = ((int)now.state);
		now.state = 1;
#ifdef VAR_RANGES
		logval("state", ((int)now.state));
#endif
		;
		/* merge: .(goto)(0, 24, 23) */
		reached[0][24] = 1;
		;
		_m = 3; goto P999; /* 2 */
	case 10: // STATE 4 - /home/slade/defi_guardian/translated_output.pml:23 - [((state==1))] (0:0:0 - 1)
		IfNotBlocked
		reached[0][4] = 1;
		if (!((((int)now.state)==1)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 11: // STATE 5 - /home/slade/defi_guardian/translated_output.pml:24 - [printf('Executing program logic...\\n')] (0:12:1 - 1)
		IfNotBlocked
		reached[0][5] = 1;
		Printf("Executing program logic...\n");
		/* merge: lock = 1(12, 6, 12) */
		reached[0][6] = 1;
		(trpt+1)->bup.oval = lock;
		lock = 1;
#ifdef VAR_RANGES
		logval("lock", lock);
#endif
		;
		_m = 3; goto P999; /* 1 */
	case 12: // STATE 7 - /home/slade/defi_guardian/translated_output.pml:29 - [((balance>=10))] (26:0:3 - 1)
		IfNotBlocked
		reached[0][7] = 1;
		if (!((now.balance>=10)))
			continue;
		/* merge: balance = (balance-10)(26, 8, 26) */
		reached[0][8] = 1;
		(trpt+1)->bup.ovals = grab_ints(3);
		(trpt+1)->bup.ovals[0] = now.balance;
		now.balance = (now.balance-10);
#ifdef VAR_RANGES
		logval("balance", now.balance);
#endif
		;
		/* merge: printf('Withdrawal successful. New balance: %d\\n',balance)(26, 9, 26) */
		reached[0][9] = 1;
		Printf("Withdrawal successful. New balance: %d\n", now.balance);
		/* merge: .(goto)(26, 13, 26) */
		reached[0][13] = 1;
		;
		/* merge: lock = 0(26, 14, 26) */
		reached[0][14] = 1;
		(trpt+1)->bup.ovals[1] = lock;
		lock = 0;
#ifdef VAR_RANGES
		logval("lock", lock);
#endif
		;
		/* merge: printf('Program execution complete.\\n')(26, 15, 26) */
		reached[0][15] = 1;
		Printf("Program execution complete.\n");
		/* merge: state = 2(26, 16, 26) */
		reached[0][16] = 1;
		(trpt+1)->bup.ovals[2] = ((int)now.state);
		now.state = 2;
#ifdef VAR_RANGES
		logval("state", ((int)now.state));
#endif
		;
		/* merge: goto :b0(26, 17, 26) */
		reached[0][17] = 1;
		;
		_m = 3; goto P999; /* 7 */
	case 13: // STATE 11 - /home/slade/defi_guardian/translated_output.pml:33 - [printf('Insufficient balance\\n')] (0:26:2 - 1)
		IfNotBlocked
		reached[0][11] = 1;
		Printf("Insufficient balance\n");
		/* merge: .(goto)(26, 13, 26) */
		reached[0][13] = 1;
		;
		/* merge: lock = 0(26, 14, 26) */
		reached[0][14] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = lock;
		lock = 0;
#ifdef VAR_RANGES
		logval("lock", lock);
#endif
		;
		/* merge: printf('Program execution complete.\\n')(26, 15, 26) */
		reached[0][15] = 1;
		Printf("Program execution complete.\n");
		/* merge: state = 2(26, 16, 26) */
		reached[0][16] = 1;
		(trpt+1)->bup.ovals[1] = ((int)now.state);
		now.state = 2;
#ifdef VAR_RANGES
		logval("state", ((int)now.state));
#endif
		;
		/* merge: goto :b0(26, 17, 26) */
		reached[0][17] = 1;
		;
		_m = 3; goto P999; /* 5 */
	case 14: // STATE 14 - /home/slade/defi_guardian/translated_output.pml:36 - [lock = 0] (0:26:2 - 3)
		IfNotBlocked
		reached[0][14] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = lock;
		lock = 0;
#ifdef VAR_RANGES
		logval("lock", lock);
#endif
		;
		/* merge: printf('Program execution complete.\\n')(26, 15, 26) */
		reached[0][15] = 1;
		Printf("Program execution complete.\n");
		/* merge: state = 2(26, 16, 26) */
		reached[0][16] = 1;
		(trpt+1)->bup.ovals[1] = ((int)now.state);
		now.state = 2;
#ifdef VAR_RANGES
		logval("state", ((int)now.state));
#endif
		;
		/* merge: goto :b0(26, 17, 26) */
		reached[0][17] = 1;
		;
		_m = 3; goto P999; /* 3 */
	case 15: // STATE 19 - /home/slade/defi_guardian/translated_output.pml:41 - [((state==2))] (0:0:0 - 1)
		IfNotBlocked
		reached[0][19] = 1;
		if (!((((int)now.state)==2)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 16: // STATE 20 - /home/slade/defi_guardian/translated_output.pml:42 - [printf('Program terminated.\\n')] (0:26:0 - 1)
		IfNotBlocked
		reached[0][20] = 1;
		Printf("Program terminated.\n");
		/* merge: goto :b0(26, 21, 26) */
		reached[0][21] = 1;
		;
		_m = 3; goto P999; /* 1 */
	case 17: // STATE 26 - /home/slade/defi_guardian/translated_output.pml:46 - [-end-] (0:0:0 - 3)
		IfNotBlocked
		reached[0][26] = 1;
		if (!delproc(1, II)) continue;
		_m = 3; goto P999; /* 0 */
	case  _T5:	/* np_ */
		if (!((!(trpt->o_pm&4) && !(trpt->tau&128))))
			continue;
		/* else fall through */
	case  _T2:	/* true */
		_m = 3; goto P999;
#undef rand
	}

