(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
    a1 - agent
    a2 - agent
    a3 - agent
    a4 - agent
)
(:init
	(handempty a1)
	(handempty a2)
	(handempty a3)
	(handempty a4)
	(clear c)
	(clear a)
	(clear b)
	(clear d)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (handempty a3)
	    (handempty a4)
		(on d c)
		(on c b)
		(on b a)
	)
)
)