from mira_runner.policy_v4 import RelativeOrderPolicy, classify_v4


def test_free_orders_do_not_use_nonfree_cap_and_round_still_advances():
    p = RelativeOrderPolicy(cap=2, endorsed=['Cardiac MRI'])
    allowed, held = p.plan(['ECG', 'Troponin', 'Cardiac MRI', 'CBC', 'TSH', 'Urinalysis'])
    assert allowed == ['ECG', 'Troponin', 'Cardiac MRI', 'CBC', 'TSH']
    assert [(x['requested'], x['why']) for x in held] == [('Urinalysis', 'cap')]
    assert p.nonfree_turn_tests == 2
    assert p.turn_tests == 5
    p.end_turn()
    assert p.rounds == 1
    assert p.nonfree_turn_tests == p.turn_tests == 0
    assert p.plan(['Urinalysis'])[0] == ['Urinalysis']


def test_critical_only_round_unlocks_tier_three_without_consuming_cap():
    p = RelativeOrderPolicy(cap=1)
    assert p.plan(['ECG', 'Troponin'])[0] == ['ECG', 'Troponin']
    assert p.nonfree_turn_tests == 0
    p.end_turn()
    assert p.plan(['MRI brain'])[0] == ['MRI brain']


def test_ldh_is_not_emergency_lactate():
    assert classify_v4('Lactate') == (1, 1, True)
    assert classify_v4('Lactate dehydrogenase') == (1, 1, False)
    assert classify_v4('LDH') == (1, 1, False)
    p = RelativeOrderPolicy(cap=1)
    assert p.plan(['CBC'])[0] == ['CBC']
    allowed, held = p.plan(['LDH', 'Lactate'])
    assert allowed == ['Lactate']
    assert held[0]['requested'] == 'LDH'


def test_coronary_endorsement_does_not_endorse_generic_or_other_angiography():
    p = RelativeOrderPolicy(cap=1, endorsed=['Coronary angiography'])
    assert p.is_endorsed('coronary angiography')
    assert not p.is_endorsed('angiography')
    assert not p.is_endorsed('pulmonary angiography')
    assert not p.is_endorsed('CT pulmonary angiography')
    allowed, held = p.plan(['Coronary angiography', 'angiography', 'pulmonary angiography'])
    assert allowed == ['Coronary angiography']
    assert {x['requested'] for x in held} == {'angiography', 'pulmonary angiography'}
    assert all(x['why'] == 'tier3' for x in held)


def test_nonfree_cap_remains_bounded_across_calls_and_next_round():
    p = RelativeOrderPolicy(cap=2)
    assert p.plan(['CBC'])[0] == ['CBC']
    assert p.plan(['TSH', 'Urinalysis'])[0] == ['TSH']
    assert p.plan(['Chest X-ray', 'CRP'])[0] == []
    p.end_turn()
    allowed, held = p.plan(['Chest X-ray', 'CRP', 'Chest CT'])
    assert allowed == ['Chest X-ray', 'CRP']
    assert held[0]['requested'] == 'Chest CT'
    assert p.nonfree_turn_tests == 2


def test_tier_three_is_held_before_any_results_and_message_has_no_dollar_price():
    p = RelativeOrderPolicy(cap=2)
    allowed, held = p.plan(['MRI brain'])
    assert not allowed and held[0]['why'] == 'tier3'
    assert p.spent == 0
    msg = p.message(allowed, held, 0)
    assert 'not performed' in msg and '15 relative units' in msg
    assert 'US$' not in msg and 'USD' not in msg
    p.plan(['ECG'])
    p.end_turn()
    allowed, held = p.plan(['MRI brain'])
    msg = p.message(allowed, held, 1300, immediate=True)
    assert '15 relative units' in msg and 'planning estimate' in msg
    assert '1300' not in msg
    assert 'spent_usd' not in p.stats


def test_synonym_endorsement_uses_exam_identity_and_never_token_overlap():
    p = RelativeOrderPolicy(endorsed=['Electrocardiogram', 'Cardiac MRI'])
    assert p.is_endorsed('ECG')
    assert p.is_endorsed('cardiac MRI')
    assert not p.is_endorsed('Brain MRI')
