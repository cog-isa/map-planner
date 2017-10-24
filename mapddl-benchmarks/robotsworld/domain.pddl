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
	:parameters (?rob - robot ?x - block ?s - size ?loc - location)
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
	:parameters (?rob - robot ?x - block ?s - size ?loc - location)
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
	:parameters (?rob - robot ?x - block ?y - block ?s - size ?loc - location)
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
	:parameters (?rob - robot ?x - block ?y - block ?s - size ?loc - location)
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

(:action drive-position
	:agent (?rob - robot)
	:parameters (?loc-to - location ?r - room)
	:precondition (and
		(at ?rob ?r)
	)
	:effect (and
		(at ?rob ?loc-to)
		(in-room ?loc-to ?r)
	)
)

(:action drive-room
	:agent (?rob - robot)
	:parameters (?loc-from - room ?loc-to - room)
	:precondition (and
		(at ?rob ?loc-from)
	)
	:effect (and
		(not (at ?rob ?loc-from))
		(at ?rob ?loc-to)
	)
)

)