(define (problem BLOCKS-1-3) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	g - block
	f - block
	z - block
    a1 - agent
    a2 - agent
    a3 - agent
    big - size
    small - size
    middle - size
    huge - size
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
	(clear g)
	(clear f)
	(clear z)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable g)
	(ontable f)
	(ontable z)
	(blocktype big g)
	(blocktype big a)
	(blocktype small b)
	(blocktype middle c)
	(blocktype small d)
	(blocktype middle e)
	(blocktype huge f)
	(blocktype huge z)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (handempty a3)
	    (on z f)
	    (on f g)
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
        (blocktype huge f)
	    (blocktype huge z)
	)
)

(:constraints
    (and

        (and (always (forall (?x - block)
            (implies (or (blocktype big ?x) (blocktype middle ?x) (blocktype huge ?x)) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype big ?x) (blocktype small ?x) (blocktype huge ?x)) (holding a2 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype middle ?x) (blocktype small ?x) (blocktype big ?x)) (holding a3 ?x))))
        )


    )
)
)


