(define (problem BLOCKS-1-3) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
    a1 - agent
    a2 - agent
    a3 - agent
    big - size
    small - size
    middle - size
)
(:init
	(handempty a1)
	(handempty a2)
	(handempty a3)
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
	(blocktype middle c)
	(blocktype small d)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (handempty a3)
		(on d c)
		(on c b)
		(on b a)
        (blocktype big a)
        (blocktype small b)
        (blocktype middle c)
        (blocktype small d)
	)
)

(:constraints
    (and

        (and (always (forall (?x - block)
            (implies (or (blocktype big ?x) (blocktype small ?x)) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype small ?x) (blocktype middle ?x)) (holding a2 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype middle ?x) (blocktype big ?x)) (holding a3 ?x))))
        )


    )
)
)


