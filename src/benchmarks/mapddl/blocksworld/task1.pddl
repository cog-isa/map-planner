(define (problem BLOCKS-1-3) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
    a1 - agent
    a2 - agent
    big - size
    small - size
)
(:init
	(handempty a1)
	(handempty a2)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(blocktype big a)
	(blocktype small b)
	(blocktype big c)
	(blocktype small d)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
		(on d c)
		(on c b)
		(on b a)
        (blocktype big a)
        (blocktype small b)
        (blocktype big c)
        (blocktype small d)
	)
)

(:constraints
    (and

        (and (always (forall (?x - block)
            (implies (blocktype big ?x)(holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype small ?x)(holding a2 ?x))))
        )

    )
)
)

