(define (problem robots-0-1) (:domain robots)
(:objects
	room1 - room
	room2 - room
	weightlifter - robot
	gambler - robot
	a - block
	b - block
	c - block
	d - block
	pos1 - location
	pos2 - location
	big - size
    small - size
	)
(:init
	(at weightlifter room1)
	(at gambler room1)
	(at a pos1)
	(at b pos1)
	(at c pos1)
	(at d pos1)
	(in-room pos1 room1)
	(in-room pos2 room2)
	(handempty weightlifter)
	(handempty gambler)
	(blocktype big a)
	(blocktype small b)
	(blocktype small d)
	(blocktype big c)
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
		(at weightlifter pos2)
	    (at gambler pos2)
	    (at a pos2)
	    (at b pos2)
	    (at c pos2)
	    (at d pos2)
	    (in-room pos1 room1)
	    (in-room pos2 room2)
	    (handempty weightlifter)
	    (handempty gambler)
	    (blocktype big a)
	    (blocktype small b)
	    (blocktype small d)
	    (blocktype big c)
	    (on d c)
		(on c b)
		(on b a)
		(ontable a)
		(clear d)
	)
)

(:constraints
    (and
        (and (always (forall (?x - block)
            (implies (blocktype big ?x) (holding weightlifter ?x))))
        )
        (and (always (forall (?x - block)
            (implies (blocktype small ?x) (holding gambler ?x))))
        )
    )
)

)