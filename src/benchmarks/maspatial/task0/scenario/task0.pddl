(define (problem BLOCKS-1-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
    ag1 - agent
    ag2 - agent
    big - size
    small - size
)
(:init
	(handempty ag1)
	(handempty ag2)
	(clear a)
	(clear b)
	(clear c)
	(ontable a)
	(ontable b)
	(ontable c)
	(blocktype big a)
	(blocktype small b)
	(blocktype big c)
)
(:goal
	(and
	    (handempty ag1)
	    (handempty ag2)
		(on b a)
		(on c b)
        (blocktype big a)
        (blocktype small b)
        (blocktype big c)
	)
)

(:constraints
    (and

        (and (always (forall (?x - block)
            (implies (blocktype big ?x)(holding ag1 ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype small ?x)(holding ag2 ?x))))
        )

    )
)
)

