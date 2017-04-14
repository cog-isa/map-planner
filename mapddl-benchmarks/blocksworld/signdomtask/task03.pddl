(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
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
	(clear e)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(blocktype big a)
	(blocktype small b)
	(blocktype middle c)
	(blocktype small d)
	(blocktype middle e)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (handempty a3)
		(on e d)
		(on d c)
		(on c a)
		(on a b)
        (blocktype big a)
        (blocktype small b)
        (blocktype middle c)
        (blocktype small d)
        (blocktype middle e)
	)
)

(:constraints
    (and
        (and (always (forall (?x - block)
            (implies (blocktype big ?x) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype small ?x) (holding a2 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype middle ?x) (holding a3 ?x))))
        )
    )
)
)


