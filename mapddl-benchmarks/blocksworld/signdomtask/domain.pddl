(define (domain blocks)
	(:requirements :typing :multi-agent :unfactored-privacy)
(:types
	agent block size - object
)
(:predicates
	(on ?x - block ?y - block)
	(ontable ?x - block)
	(clear ?x - block)
    (holding ?ag - agent ?x - block)
    (handempty ?ag - agent)
    (blocktype ?s - size ?x - block)
)

(:action pick-up
	:parameters (?ag - agent ?x - block ?s - size)
	:precondition (and
		(clear ?x)
		(ontable ?x)
		(handempty ?ag)
		(blocktype ?s ?x)
	)
	:effect (and
		(not (ontable ?x))
		(not (clear ?x))
		(not (handempty ?ag))
		(holding ?ag ?x)
		(blocktype ?s ?x)
	)
)


(:action put-down
	:parameters (?ag - agent ?x - block ?s - size)
	:precondition (and
		(holding ?ag ?x)
		(blocktype ?s ?x)
	)
	:effect (and
		(not (holding ?ag ?x))
		(clear ?x)
		(handempty ?ag)
		(ontable ?x)
		(blocktype ?s ?x)
	)
)


(:action stack
	:parameters (?ag - agent ?x - block ?y - block ?s - size)
	:precondition (and
		(holding ?ag ?x)
		(clear ?y)
		(blocktype ?s ?x)
	)
	:effect (and
		(not (holding ?ag ?x))
		(not (clear ?y))
		(clear ?x)
		(handempty ?ag)
		(on ?x ?y)
		(blocktype ?s ?x)
	)
)


(:action unstack
	:parameters (?ag - agent ?x - block ?y - block ?s - size)
	:precondition (and
		(on ?x ?y)
		(clear ?x)
		(handempty ?ag)
		(blocktype ?s ?x)
	)
	:effect (and
		(holding ?ag ?x)
		(clear ?y)
		(not (clear ?x))
		(not (handempty ?ag))
		(not (on ?x ?y))
		(blocktype ?s ?x)
	)
)

(:action wait
    :parameters (?ag - agent)
    :precondition (and
        (handempty ?ag)
    )
    :effect (and
        (handempty ?ag)
    )
)

)