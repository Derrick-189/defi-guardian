	switch (t->back) {
	default: Uerror("bad return move");
	case  0: goto R999; /* nothing to undo */

		 /* CLAIM invariant_stable */
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
		
	case 11: // STATE 10
		;
		now.state = trpt->bup.ovals[2];
		now.lock = trpt->bup.ovals[1];
		now.lock = trpt->bup.ovals[0];
		;
		ungrab_ints(trpt->bup.ovals, 3);
		goto R999;
;
		;
		;
		
	case 13: // STATE 14
		goto R999;

	case 14: // STATE 20
		;
		p_restor(II);
		;
		;
		goto R999;
	}

