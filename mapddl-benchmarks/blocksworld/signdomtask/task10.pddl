(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	g - block
	f - block
	j - block
	h - block
	z - block
    a1 - agent
    a2 - agent
    a3 - agent
    a4 - agent
    big - size
    small - size
    middle - size
    huge - size
    gigant - size
)
(:init
	(handempty a1)
	(handempty a2)
	(handempty a3)
	(handempty a4)
	(clear f)
	(clear j)
	(clear h)
	(clear z)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(clear e)
	(clear g)
	(ontable j)
	(ontable h)
	(ontable z)
	(ontable f)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable g)
	(blocktype huge f)
	(blocktype gigant h)
	(blocktype huge z)
	(blocktype gigant j)
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
	    (handempty a4)
	    (on j z)
	    (on z h)
	    (on h f)
	    (on f g)
	    (on g e)
		(on e d)
		(on d c)
		(on c b)
		(on b a)
		(blocktype huge f)
	    (blocktype gigant h)
	    (blocktype huge z)
	    (blocktype gigant j)
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
            (implies (or (blocktype huge ?x) (blocktype big ?x)) (holding a1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype small ?x) (blocktype gigant ?x)) (holding a2 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (or (blocktype gigant ?x) (blocktype middle ?x)) (holding a3 ?x))))
        )

        (and (always (forall (?x - block)
            (implies (or (blocktype big ?x) (blocktype middle ?x) (blocktype small ?x)) (holding a4 ?x))))
        )


    )
)
)


