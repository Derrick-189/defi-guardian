	switch (t->back) {
	default: Uerror("bad return move");
	case  0: goto R999; /* nothing to undo */

		 /* PROC User */

	case 3: // STATE 1
		;
		((P1 *)_this)->action = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;
;
		;
		
	case 5: // STATE 4
		;
		now.total_liquidity = trpt->bup.ovals[1];
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;

	case 6: // STATE 10
		;
		((P1 *)_this)->action = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;
;
		;
		
	case 8: // STATE 13
		;
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = trpt->bup.ovals[1];
		now.total_liquidity = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;

	case 9: // STATE 19
		;
		((P1 *)_this)->action = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;
;
		;
		
	case 11: // STATE 22
		;
		now.users[ Index(((P1 *)_this)->id, 2) ].debt = trpt->bup.ovals[1];
		now.total_liquidity = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;

	case 12: // STATE 28
		;
		((P1 *)_this)->action = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;
;
		;
		
	case 14: // STATE 32
		;
		now.total_liquidity = trpt->bup.ovals[2];
		now.users[ Index(((P1 *)_this)->id, 2) ].debt = trpt->bup.ovals[1];
		now.users[ Index(((P1 *)_this)->id, 2) ].balance = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 3);
		goto R999;

	case 15: // STATE 41
		;
		p_restor(II);
		;
		;
		goto R999;

		 /* PROC :init: */

	case 16: // STATE 2
		;
		now.users[1].balance = trpt->bup.ovals[1];
		now.users[0].balance = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;

	case 17: // STATE 4
		;
		;
		delproc(0, now._nr_pr-1);
		;
		goto R999;

	case 18: // STATE 5
		;
		;
		delproc(0, now._nr_pr-1);
		;
		goto R999;

	case 19: // STATE 6
		;
		p_restor(II);
		;
		;
		goto R999;
	}

