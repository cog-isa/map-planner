(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
    a1 - agent
    a2 - agent
    huge - size
    small - size
)
(:init
	(handempty a1)
	(handempty a2)
	(on d c)
	(clear a)
	(clear b)
	(clear d)
	(ontable c)
	(ontable a)
	(ontable b)
	(blocktype huge a)
	(blocktype small b)
	(blocktype huge c)
	(blocktype small d)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
		(on d c)
		(on c b)
		(on b a)
        (blocktype huge a)
        (blocktype small b)
        (blocktype huge c)
        (blocktype small d)
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


