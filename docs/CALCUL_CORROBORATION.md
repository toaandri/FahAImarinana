# Calcul de corroboration des sources

Après une pré-analyse, le journaliste saisit une affirmation précise et les URL
des sources qu’il a lues. Il indique pour chaque source si elle confirme,
contredit ou ne permet pas de conclure sur cette même affirmation.

Le calcul regroupe les sous-domaines partageant les deux derniers segments du
nom de domaine ; plusieurs liens du même groupe ne comptent qu’une fois. Si les
appréciations d’un même groupe divergent, ce groupe est non concluant. Ce
regroupement est volontairement conservateur : il peut fusionner des médias
différents sous un même suffixe, par exemple `co.uk`.

Avec au moins deux groupes conclusifs :

`corroboration = 100 × groupes confirmant / (groupes confirmant + groupes contredisant)`

Les groupes non concluants sont présentés mais exclus du dénominateur. En dessous
de deux groupes conclusifs, aucun pourcentage n’est calculé. Un résultat de 100 %
signifie que tous les groupes conclusifs saisis confirment l’affirmation ; il ne
signifie pas que celle-ci a 100 % de chances d’être vraie.

Le calcul ne consulte pas les URL et ne vérifie ni les jugements saisis, ni
l’indépendance éditoriale, ni la fiabilité des sources. Le journaliste doit
notamment vérifier les reprises de dépêche, l’origine, les dates et le contexte.
Le résultat reste dans l’écran et n’est pas enregistré comme verdict éditorial.
