(define (domain robots)
	(:requirements :typing :multi-agent)
(:types
	location robot block size - object
	room - location
)
(:predicates
	(on ?x - block ?y - block)
	(ontable ?x - block)
	(clear ?x - block)
    (holding ?rob - robot ?x - block)
    (handempty ?rob - robot)
    (blocktype ?s - size ?x - block)
    (at ?obj - object ?loc - location)
    (in-room ?loc - location ?r - room)
)

(:action pick-up
    :agent (?rob - robot)
	:parameters (?x - block ?s - size ?loc - location)
	:precondition (and
		(clear ?x)
		(ontable ?x)
		(handempty ?rob)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?rob ?loc)
	)
	:effect (and
		(not (ontable ?x))
		(not (clear ?x))
		(not (handempty ?rob))
		(holding ?rob ?x)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?rob ?loc)
	)
)


(:action put-down
    :agent (?rob - robot)
	:parameters (?x - block ?s - size ?loc - location)
	:precondition (and
		(holding ?rob ?x)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?rob ?loc)
	)
	:effect (and
		(not (holding ?rob ?x))
		(clear ?x)
		(handempty ?rob)
		(ontable ?x)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?rob ?loc)
	)
)


(:action stack
    :agent (?rob - robot)
	:parameters (?x - block ?y - block ?s - size ?loc - location)
	:precondition (and
		(holding ?rob ?x)
		(clear ?y)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?y ?loc)
		(at ?rob ?loc)
	)
	:effect (and
		(not (holding ?rob ?x))
		(not (clear ?y))
		(clear ?x)
		(handempty ?rob)
		(on ?x ?y)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?y ?loc)
		(at ?rob ?loc)
	)
)


(:action unstack
    :agent (?rob - robot)
	:parameters (?x - block ?y - block ?s - size ?loc - location)
	:precondition (and
		(on ?x ?y)
		(clear ?x)
		(handempty ?rob)
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?y ?loc)
		(at ?rob ?loc)
	)
	:effect (and
		(holding ?rob ?x)
		(clear ?y)
		(not (clear ?x))
		(not (handempty ?rob))
		(not (on ?x ?y))
		(blocktype ?s ?x)
		(at ?x ?loc)
		(at ?y ?loc)
		(at ?rob ?loc)
	)
)

(:action drive-position-empty
	:agent (?rob - robot)
	:parameters (?loc-to - location ?r - room)
	:precondition (and
	    (handempty ?rob)
		(at ?rob ?r)
	)
	:effect (and
		(at ?rob ?loc-to)
		(in-room ?loc-to ?r)
		(handempty ?rob)
	)
)

(:action drive-room-empty
	:agent (?rob - robot)
	:parameters (?loc-from - room ?loc-to - room)
	:precondition (and
		(at ?rob ?loc-from)
		(handempty ?rob)
	)
	:effect (and
		(not (at ?rob ?loc-from))
		(at ?rob ?loc-to)
		(handempty ?rob)
	)
)

(:action carry-to-position
	:agent (?rob - robot)
	:parameters (?loc-to - location ?r - room ?x - block ?s - size)
	:precondition (and
	    (holding ?rob ?x)
		(at ?rob ?r)
		(at ?x ?r)
		(blocktype ?s ?x)
	)
	:effect (and
		(at ?rob ?loc-to)
		(at ?x ?loc-to)
		(in-room ?loc-to ?r)
		(holding ?rob ?x)
		(blocktype ?s ?x)
	)
)

(:action carry-to-room
	:agent (?rob - robot)
	:parameters (?loc-from - room ?loc-to - room ?x - block ?s - size)
	:precondition (and
	    (holding ?rob ?x)
		(at ?rob ?loc-from)
		(at ?rob ?loc-from)
		(blocktype ?s ?x)
	)
	:effect (and
		(not(at ?rob ?loc-from))
		(not(at ?x ?loc-from))
		(at ?rob ?loc-to)
		(at ?x ?loc-to)
		(holding ?rob ?x)
		(blocktype ?s ?x)
	)
)

)