(define (problem BLOCKS-0-2-1) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	h - block
    a1 - agent
    a2 - agent
    huge - size
    small - size
)(:init
	(handempty a1)
	(handempty a2)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(clear e)
	(clear h)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable h)
	(blocktype small h)
	(blocktype huge a)
	(blocktype small b)
	(blocktype huge c)
	(blocktype small d)
	(blocktype huge e)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (on h e)
		(on e d)
		(on d c)
		(on c b)
		(on b a)
		(blocktype small h)
        (blocktype huge a)
        (blocktype small b)
        (blocktype huge c)
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


