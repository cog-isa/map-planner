(define (problem BLOCKS-0-6) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	g - block
	f - block
	h - block
    a1 - agent
    a2 - agent
    a3 - agent
    a4 - agent
    huge - size
    small - size
    middle - size
    gigant - size
)
(:init
	(handempty a1)
	(handempty a2)
	(handempty a3)
	(handempty a4)
	(clear f)
	(clear h)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(clear e)
	(clear g)
	(ontable f)
	(ontable h)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable g)
	(blocktype gigant f)
	(blocktype gigant h)
	(blocktype huge g)
	(blocktype huge a)
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
	    (on h f)
	    (on f g)
	    (on g e)
		(on e d)
		(on d c)
		(on c b)
		(on b a)
		(blocktype gigant f)
	    (blocktype gigant h)
        (blocktype huge g)
        (blocktype huge a)
        (blocktype small b)
        (blocktype middle c)
        (blocktype small d)
        (blocktype middle e)
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
        (and (always (forall (?x - block)
            (implies (blocktype middle ?x) (holding a3 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype gigant ?x) (holding a4 ?x))))
        )
    )
)
)


