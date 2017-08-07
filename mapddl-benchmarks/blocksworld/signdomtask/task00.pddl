(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
    a1 - agent
    huge - size
)
(:init
	(handempty a1)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(blocktype huge a)
	(blocktype huge b)
	(blocktype huge c)
	(blocktype huge d)
)
(:goal
	(and
	    (handempty a1)
		(on d c)
		(on c b)
		(on b a)
        (blocktype huge a)
        (blocktype huge b)
        (blocktype huge c)
        (blocktype huge d)
	)
)

(:constraints
    (and
        (and (always (forall (?x - block)
            (implies (blocktype huge ?x) (holding a1 ?x))))
        )
    )
)
)


