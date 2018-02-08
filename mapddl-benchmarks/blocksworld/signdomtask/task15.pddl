(define (problem BLOCKS-1-5) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	g - block
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
	(clear a)
	(clear b)
	(clear d)
	(clear e)
	(clear g)
	(ontable c)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable g)
	(on a c)
	(blocktype big g)
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
	    (on g e)
		(on e d)
		(on d c)
		(on c b)
		(on b a)
        (blocktype big g)
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
            (implies (or (blocktype big ?x) (blocktype middle ?x)) (holding a3 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype big ?x) (blocktype small ?x)) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype middle ?x) (blocktype small ?x)) (holding a2 ?x))))
        )
    )
)
)
