(define (problem BLOCKS-4-0) (:domain blocks)
(:objects
	a - block
	c - block
	b - block
	d - block
	e - block
	f - block
	i - block
	g - block
    a1 - agent
    a2 - agent
    a3 - agent
    a4 - agent
    red - type
    green - type
    blue - type
    black - type
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
	(clear e)
	(clear f)
	(clear g)
	(clear i)
	(ontable c)
	(ontable a)
	(ontable b)
	(ontable d)
	(ontable e)
	(ontable f)
	(ontable g)
	(ontable i)
)
(:goal
	(and
	    (handempty a1)
	    (handempty a2)
	    (handempty a3)
	    (handempty a4)
	    (on g i)
	    (on i f)
	    (on f e)
	    (on e d)
		(on d c)
		(on c b)
		(on b a)
	)
)
)