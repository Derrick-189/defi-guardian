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

		 /* PROC User */
	case 3: // STATE 1 - /home/slade/defi_guardian/translated_output.pml:34 - [action = 1] (0:0:2 - 1)
		IfNotBlocked
		reached[1][1] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((P1 *)_this)->action;
		((P1 *)_this)->action = 1;
#ifdef VAR_RANGES
		logval("User:action", ((P1 *)_this)->action);
#endif
		;
		if (TstOnly) return 1; /* TT */
		/* dead 2: action */  
#ifdef HAS_CODE
		if (!readtrail)
#endif
			((P1 *)_this)->action = 0;
		_m = 3; goto P999; /* 0 */
	case 4: // STATE 2 - /home/slade/defi_guardian/translated_output.pml:36 - [((users[id].balance>0))] (0:0:0 - 1)
		IfNotBlocked
		reached[1][2] = 1;
		if (!((now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance>0)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 5: // STATE 3 - /home/slade/defi_guardian/translated_output.pml:38 - [users[id].balance = (users[id].balance-10)] (0:38:2 - 1)
		IfNotBlocked
		reached[1][3] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance;
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = (now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance-10);
#ifdef VAR_RANGES
		logval("users[User:id].balance", now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance);
#endif
		;
		/* merge: total_liquidity = (total_liquidity+10)(38, 4, 38) */
		reached[1][4] = 1;
		(trpt+1)->bup.ovals[1] = ((int)now.total_liquidity);
		now.total_liquidity = (((int)now.total_liquidity)+10);
#ifdef VAR_RANGES
		logval("total_liquidity", ((int)now.total_liquidity));
#endif
		;
		/* merge: .(goto)(0, 9, 38) */
		reached[1][9] = 1;
		;
		/* merge: .(goto)(0, 39, 38) */
		reached[1][39] = 1;
		;
		_m = 3; goto P999; /* 3 */
	case 6: // STATE 10 - /home/slade/defi_guardian/translated_output.pml:44 - [action = 2] (0:0:2 - 1)
		IfNotBlocked
		reached[1][10] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((P1 *)_this)->action;
		((P1 *)_this)->action = 2;
#ifdef VAR_RANGES
		logval("User:action", ((P1 *)_this)->action);
#endif
		;
		if (TstOnly) return 1; /* TT */
		/* dead 2: action */  
#ifdef HAS_CODE
		if (!readtrail)
#endif
			((P1 *)_this)->action = 0;
		_m = 3; goto P999; /* 0 */
	case 7: // STATE 11 - /home/slade/defi_guardian/translated_output.pml:46 - [((total_liquidity>=10))] (0:0:0 - 1)
		IfNotBlocked
		reached[1][11] = 1;
		if (!((((int)now.total_liquidity)>=10)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 8: // STATE 12 - /home/slade/defi_guardian/translated_output.pml:48 - [total_liquidity = (total_liquidity-10)] (0:38:2 - 1)
		IfNotBlocked
		reached[1][12] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((int)now.total_liquidity);
		now.total_liquidity = (((int)now.total_liquidity)-10);
#ifdef VAR_RANGES
		logval("total_liquidity", ((int)now.total_liquidity));
#endif
		;
		/* merge: users[id].balance = (users[id].balance+10)(38, 13, 38) */
		reached[1][13] = 1;
		(trpt+1)->bup.ovals[1] = now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance;
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = (now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance+10);
#ifdef VAR_RANGES
		logval("users[User:id].balance", now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance);
#endif
		;
		/* merge: .(goto)(0, 18, 38) */
		reached[1][18] = 1;
		;
		/* merge: .(goto)(0, 39, 38) */
		reached[1][39] = 1;
		;
		_m = 3; goto P999; /* 3 */
	case 9: // STATE 19 - /home/slade/defi_guardian/translated_output.pml:54 - [action = 3] (0:0:2 - 1)
		IfNotBlocked
		reached[1][19] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((P1 *)_this)->action;
		((P1 *)_this)->action = 3;
#ifdef VAR_RANGES
		logval("User:action", ((P1 *)_this)->action);
#endif
		;
		if (TstOnly) return 1; /* TT */
		/* dead 2: action */  
#ifdef HAS_CODE
		if (!readtrail)
#endif
			((P1 *)_this)->action = 0;
		_m = 3; goto P999; /* 0 */
	case 10: // STATE 20 - /home/slade/defi_guardian/translated_output.pml:56 - [((total_liquidity>=50))] (0:0:0 - 1)
		IfNotBlocked
		reached[1][20] = 1;
		if (!((((int)now.total_liquidity)>=50)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 11: // STATE 21 - /home/slade/defi_guardian/translated_output.pml:58 - [total_liquidity = (total_liquidity-50)] (0:38:2 - 1)
		IfNotBlocked
		reached[1][21] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((int)now.total_liquidity);
		now.total_liquidity = (((int)now.total_liquidity)-50);
#ifdef VAR_RANGES
		logval("total_liquidity", ((int)now.total_liquidity));
#endif
		;
		/* merge: users[id].debt = (users[id].debt+50)(38, 22, 38) */
		reached[1][22] = 1;
		(trpt+1)->bup.ovals[1] = now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt;
		now.users[ Index(((P1 *)_this)->id, 2) ].debt = (now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt+50);
#ifdef VAR_RANGES
		logval("users[User:id].debt", now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt);
#endif
		;
		/* merge: .(goto)(0, 27, 38) */
		reached[1][27] = 1;
		;
		/* merge: .(goto)(0, 39, 38) */
		reached[1][39] = 1;
		;
		_m = 3; goto P999; /* 3 */
	case 12: // STATE 28 - /home/slade/defi_guardian/translated_output.pml:64 - [action = 4] (0:0:2 - 1)
		IfNotBlocked
		reached[1][28] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = ((P1 *)_this)->action;
		((P1 *)_this)->action = 4;
#ifdef VAR_RANGES
		logval("User:action", ((P1 *)_this)->action);
#endif
		;
		if (TstOnly) return 1; /* TT */
		/* dead 2: action */  
#ifdef HAS_CODE
		if (!readtrail)
#endif
			((P1 *)_this)->action = 0;
		_m = 3; goto P999; /* 0 */
	case 13: // STATE 29 - /home/slade/defi_guardian/translated_output.pml:66 - [(((users[id].debt>0)&&(users[id].balance>=55)))] (0:0:0 - 1)
		IfNotBlocked
		reached[1][29] = 1;
		if (!(((now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt>0)&&(now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance>=55))))
			continue;
		_m = 3; goto P999; /* 0 */
	case 14: // STATE 30 - /home/slade/defi_guardian/translated_output.pml:68 - [users[id].balance = (users[id].balance-55)] (0:38:3 - 1)
		IfNotBlocked
		reached[1][30] = 1;
		(trpt+1)->bup.ovals = grab_ints(3);
		(trpt+1)->bup.ovals[0] = now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance;
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = (now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance-55);
#ifdef VAR_RANGES
		logval("users[User:id].balance", now.users[ Index(((int)((P1 *)_this)->id), 2) ].balance);
#endif
		;
		/* merge: users[id].debt = (users[id].debt-50)(38, 31, 38) */
		reached[1][31] = 1;
		(trpt+1)->bup.ovals[1] = now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt;
		now.users[ Index(((P1 *)_this)->id, 2) ].debt = (now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt-50);
#ifdef VAR_RANGES
		logval("users[User:id].debt", now.users[ Index(((int)((P1 *)_this)->id), 2) ].debt);
#endif
		;
		/* merge: total_liquidity = (total_liquidity+55)(38, 32, 38) */
		reached[1][32] = 1;
		(trpt+1)->bup.ovals[2] = ((int)now.total_liquidity);
		now.total_liquidity = (((int)now.total_liquidity)+55);
#ifdef VAR_RANGES
		logval("total_liquidity", ((int)now.total_liquidity));
#endif
		;
		/* merge: .(goto)(0, 37, 38) */
		reached[1][37] = 1;
		;
		/* merge: .(goto)(0, 39, 38) */
		reached[1][39] = 1;
		;
		_m = 3; goto P999; /* 4 */
	case 15: // STATE 41 - /home/slade/defi_guardian/translated_output.pml:75 - [-end-] (0:0:0 - 1)
		IfNotBlocked
		reached[1][41] = 1;
		if (!delproc(1, II)) continue;
		_m = 3; goto P999; /* 0 */

		 /* PROC :init: */
	case 16: // STATE 1 - /home/slade/defi_guardian/translated_output.pml:20 - [users[0].balance = 100] (0:4:2 - 1)
		IfNotBlocked
		reached[0][1] = 1;
		(trpt+1)->bup.ovals = grab_ints(2);
		(trpt+1)->bup.ovals[0] = now.users[0].balance;
		now.users[0].balance = 100;
#ifdef VAR_RANGES
		logval("users[0].balance", now.users[0].balance);
#endif
		;
		/* merge: users[1].balance = 100(4, 2, 4) */
		reached[0][2] = 1;
		(trpt+1)->bup.ovals[1] = now.users[1].balance;
		now.users[1].balance = 100;
#ifdef VAR_RANGES
		logval("users[1].balance", now.users[1].balance);
#endif
		;
		_m = 3; goto P999; /* 1 */
	case 17: // STATE 4 - /home/slade/defi_guardian/translated_output.pml:25 - [(run User(0))] (0:0:0 - 1)
		IfNotBlocked
		reached[0][4] = 1;
		if (!(addproc(II, 1, 1, 0)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 18: // STATE 5 - /home/slade/defi_guardian/translated_output.pml:26 - [(run User(1))] (0:0:0 - 1)
		IfNotBlocked
		reached[0][5] = 1;
		if (!(addproc(II, 1, 1, 1)))
			continue;
		_m = 3; goto P999; /* 0 */
	case 19: // STATE 6 - /home/slade/defi_guardian/translated_output.pml:27 - [-end-] (0:0:0 - 1)
		IfNotBlocked
		reached[0][6] = 1;
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

