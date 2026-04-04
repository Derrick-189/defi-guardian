	switch (t->back) {
	default: Uerror("bad return move");
	case  0: goto R999; /* nothing to undo */

		 /* CLAIM invariant_balance */
;
		
	case 3: // STATE 1
		goto R999;

	case 4: // STATE 10
		;
		p_restor(II);
		;
		;
		goto R999;

		 /* CLAIM liveness_progress */
;
		;
		
	case 6: // STATE 6
		;
		p_restor(II);
		;
		;
		goto R999;

		 /* CLAIM safety_no_overflow */
;
		
	case 7: // STATE 1
		goto R999;

	case 8: // STATE 10
		;
		p_restor(II);
		;
		;
		goto R999;

		 /* PROC Program */

	case 9: // STATE 2
		;
		now.state = trpt->bup.oval;
		;
		goto R999;
;
		;
		
	case 11: // STATE 6
		;
		lock = trpt->bup.oval;
		;
		goto R999;

	case 12: // STATE 16
		;
		now.state = trpt->bup.ovals[2];
		lock = trpt->bup.ovals[1];
		now.balance = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 3);
		goto R999;

	case 13: // STATE 16
		;
		now.state = trpt->bup.ovals[1];
		lock = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;

	case 14: // STATE 16
		;
		now.state = trpt->bup.ovals[1];
		lock = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 2);
		goto R999;
;
		;
		;
		
	case 16: // STATE 20
		goto R999;

	case 17: // STATE 26
		;
		p_restor(II);
		;
		;
		goto R999;
	}

