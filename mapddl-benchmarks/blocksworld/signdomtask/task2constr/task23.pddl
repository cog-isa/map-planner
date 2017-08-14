(define (problem BLOCKS-0-2-3) (:domain blocks)
(:objects
	d - block
	e - block
	h - block
	f - block
    a1 - agent
    a2 - agent
    huge - size
    small - size
)(:init
	(handempty a1)
	(handempty a2)
	(clear d)
	(clear e)
	(clear h)
	(clear f)
	(ontable f)
	(ontable d)
	(ontable e)
	(ontable h)
	(blocktype huge f)
	(blocktype small h)
	(blocktype small d)
	(blocktype huge e)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (on h e)
		(on e d)
		(on d f)
		(blocktype huge f)
		(blocktype small h)
        (blocktype small d)
        (blocktype huge e)
	)
)

(:constraints
    (and
        (and (always (forall (?x - block)
            (implies (blocktype huge ?x) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype small ?x) (holding a2 ?x))))
        )
    )
)
)
