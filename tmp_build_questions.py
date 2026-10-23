import json
import os
import re
from pathlib import Path

root = Path(r'd:\Program Files (x86)\SubLadder')
old_dir = root / 'oldfiles'
questions_dir = root / 'data' / 'questions'
questions_dir.mkdir(parents=True, exist_ok=True)

old_fr_path = old_dir / 'fr_questions.json'
old_en_path = old_dir / 'en_questions.json'

with open(old_fr_path, 'r', encoding='utf-8') as f:
    fr_data = json.load(f)
with open(old_en_path, 'r', encoding='utf-8') as f:
    en_data = json.load(f)

fr_questions = fr_data.get('questions', [])
en_questions = en_data.get('questions', [])

# Build a mapping from original English question text to unique ids for duplicate prevention.
existing_ids = set()
for q in fr_questions:
    existing_ids.add(q.get('id'))

# Determine the French question pool to keep.
# We will create a new French file with the old French questions, and a new English file with the old English questions.
# Each French question will be translated into English and paired with the same id in the English file.
# For expression-like questions, we will omit them if not safely translatable.

# Heuristic: keep questions that are not clearly expression-based / idiomatic.
EXPRESSION_HINTS = (
    'What does', 'What is the meaning', 'Which is the correct spelling', 'What is the name of the',
    'In which', 'Who wrote', 'Which author', 'Which composer', 'Which film', 'Which band', 'Which country',
    'Which element', 'In what year', 'How many', 'How much', 'Who painted', 'Who directed', 'Who was',
    'What force', 'What gas', 'What is the', 'What are the', 'What was the', 'What year', 'What color',
    'Why', 'When', 'Where', 'How', 'Who', 'Which', 'In Homer's', 'In which Shakespeare', 'In Euler',
)

# We will preserve the original structure and content, but the new English file will be built from French and vice versa.
# For now, we'll create a balanced bilingual pair using the existing English question texts as the source for English.
# For any French question where a direct equivalent exists in English, we keep it as a translated question.
# For the rest, we keep the original French question content and translate it manually where possible.

# Since the request asks for the old files to be moved and new files recreated, we can create new bilingual files based on the existing pool.
# The practical approach is:
# - new fr_questions.json: old French questions, but with the question text translated to French where possible from English when the original French question is not present.
# - new en_questions.json: old English questions, but with the question text translated to English where possible from French when the original English question is not present.

# For the purpose of actual gameplay, we need a valid file. We'll produce a balanced set by taking the union of the old English and French pools,
# keeping the same ids and level metadata, and translating question text when a direct equivalent exists in the other file.
# We will omit a subset of expression/idiom questions where the translation is not safe.

# Create a simple bilingual map by id number.
fr_by_num = {}
for q in fr_questions:
    m = re.search(r'Q(\d+)$', q.get('id',''))
    if m:
        fr_by_num[int(m.group(1))] = q

en_by_num = {}
for q in en_questions:
    m = re.search(r'Q(\d+)$', q.get('id',''))
    if m:
        en_by_num[int(m.group(1))] = q

# Create the new French pool from the old French questions and add translated questions from the English pool when absent.
new_fr_questions = []
new_fr_ids = set()
for q in fr_questions:
    q_copy = json.loads(json.dumps(q))
    q_copy['id'] = q_copy['id'].replace('fr_', 'fr_')
    new_fr_questions.append(q_copy)
    new_fr_ids.add(q_copy['id'])

# Add English questions that are not already covered and where the content is not expression-like.
for num in sorted(en_by_num.keys()):
    en_q = en_by_num[num]
    # Skip obvious expression-like questions.
    text = en_q.get('question', '')
    if any(h in text for h in ['"', '’', '…', 'May the Force', 'What is the name of', 'What is the', 'How many', 'How much']):
        continue
    if en_q.get('id') in new_fr_ids:
        continue
    # Use a simple English->French translation map for the common cases.
    translations = {
        'How many sides does a triangle have?': 'Combien de côtés a un triangle ?',
        'What color do you get by mixing blue and yellow?': 'De quelle couleur obtient-on en mélangeant le bleu et le jaune ?',
        'Which animal is known as Man\'s best friend?': 'Quel animal est connu comme le meilleur ami de l\'homme ?',
        'How many months are in a year?': 'Combien de mois y a-t-il dans une année ?',
        'What shape has four equal sides and four right angles?': 'Quelle forme a quatre côtés égaux et quatre angles droits ?',
        'What do bees produce?': 'Que produisent les abeilles ?',
        'How many hours are in a day?': 'Combien d\'heures y a-t-il dans une journée ?',
        'Which primary color is the sky on a clear day?': 'Quelle couleur primaire a le ciel par temps clair ?',
        'What is the capital of France?': 'Quelle est la capitale de la France ?',
        'What is the largest planet in our solar system?': 'Quelle est la plus grande planète de notre système solaire ?',
        'How many days are in a leap year?': 'Combien de jours y a-t-il dans une année bissextile ?',
        'How many players are on a football (soccer) team on the pitch?': 'Combien de joueurs composent une équipe de football sur le terrain ?',
        'On which continent is the Amazon rainforest?': 'Sur quel continent se trouve la forêt amazonienne ?',
        'How many legs does a spider have?': 'Combien de pattes a une araignée ?',
        'What is the capital of the United Kingdom?': 'Quelle est la capitale du Royaume-Uni ?',
        'How many colors are in a rainbow?': 'Combien de couleurs y a-t-il dans un arc-en-ciel ?',
        'What is the chemical symbol for water?': 'Quel est le symbole chimique de l\'eau ?',
        'Which sport uses a shuttlecock?': 'Quel sport utilise un volant ?',
        'Which country is known as the Land of the Rising Sun?': 'Quel pays est connu comme le pays du Soleil levant ?',
        'In which film does Jack Sparrow appear?': 'Dans quel film apparaît Jack Sparrow ?',
        'What is the tallest type of grass in the world?': 'Quel est le type de graminée le plus grand au monde ?',
        'How many notes are in a musical octave?': 'Combien de notes y a-t-il dans une octave musicale ?',
        'How many continents are there on Earth?': 'Combien y a-t-il de continents sur Terre ?',
        'What force keeps us on the surface of the Earth?': 'Quelle force nous maintient à la surface de la Terre ?',
        'Who painted the Mona Lisa?': 'Qui a peint La Joconde ?',
        'How many strings does a standard guitar have?': 'Combien de cordes a une guitare standard ?',
        'What is the hardest natural substance on Earth?': 'Quelle est la substance naturelle la plus dure sur Terre ?',
        'What is the capital of Australia?': 'Quelle est la capitale de l\'Australie ?',
        'Which planet is closest to the Sun?': 'Quelle planète est la plus proche du Soleil ?',
        'In which country was Christopher Columbus born?': 'Dans quel pays Christophe Colomb est-il né ?',
        'What is the atomic number of Carbon?': 'Quel est le numéro atomique du carbone ?',
        'In which year was the Eiffel Tower completed?': 'En quelle année la tour Eiffel a-t-elle été achevée ?',
        'In what year did World War II end?': 'En quelle année la Seconde Guerre mondiale s\'est-elle terminée ?',
        'What is the longest river in the world?': 'Quel est le plus long fleuve du monde ?',
        'Which element has the chemical symbol Au?': 'Quel élément a pour symbole chimique Au ?',
        'In which sport do you use a puck?': 'Dans quel sport utilise-t-on une rondelle ?',
        'In what year did the French Revolution begin?': 'En quelle année la Révolution française a-t-elle commencé ?',
        'What is the chemical symbol for Silver?': 'Quel est le symbole chimique de l\'argent ?',
        'Who wrote The Divine Comedy?': 'Qui a écrit La Divine Comédie ?',
        'How many bones are in the adult human body?': 'Combien d\'os compte le corps humain adulte ?',
        'Who was the first person to walk on the Moon?': 'Qui a été la première personne à marcher sur la Lune ?',
        'Which band released Dark Side of the Moon?': 'Quel groupe a sorti Dark Side of the Moon ?',
        'What gas do plants absorb during photosynthesis?': 'Quel gaz les plantes absorbent-elles pendant la photosynthèse ?',
        'What is the powerhouse of the cell?': 'Quel est le centre de contrôle de la cellule ?',
        'Which empire was ruled by Genghis Khan?': 'Quel empire a été dirigé par Genghis Khan ?',
        'What is the capital of New Zealand?': 'Quelle est la capitale de la Nouvelle-Zélande ?',
        'Who directed 2001: A Space Odyssey?': 'Qui a réalisé 2001, l\'Odyssée de l\'espace ?',
        'Who wrote Romeo and Juliet?': 'Qui a écrit Roméo et Juliette ?',
        'What is the approximate speed of light?': 'Quelle est la vitesse approximative de la lumière ?',
        'In which series does Master Chief appear?': 'Dans quelle série apparaît Master Chief ?',
        'Which is the world\'s largest ocean?': 'Quel est le plus grand océan du monde ?',
        'What is the chemical formula for table salt?': 'Quelle est la formule chimique du sel de table ?',
        'In which century did the Renaissance begin in Italy?': 'Au cours de quel siècle la Renaissance a-t-elle commencé en Italie ?',
        'How many keys does a standard piano have?': 'Combien de touches a un piano standard ?',
        'In which novel does Atticus Finch appear?': 'Dans quel roman apparaît Atticus Finch ?',
        'In what year did the Berlin Wall fall?': 'En quelle année le mur de Berlin est-il tombé ?',
        'How many chambers does the human heart have?': 'Combien de cavités a le cœur humain ?',
        'What is the smallest country in the world by area?': 'Quel est le plus petit pays du monde par superficie ?',
        'Who directed Jurassic Park (1993)?': 'Qui a réalisé Jurassic Park (1993) ?',
        'What is the boiling point of water at sea level?': 'Quel est le point d\'ébullition de l\'eau au niveau de la mer ?',
        'Who was the last Tsar of Russia?': 'Qui a été le dernier tsar de Russie ?',
        'Which country has the most natural lakes in the world?': 'Quel pays possède le plus de lacs naturels au monde ?',
        'What year was the first Super Mario Bros. released in Japan?': 'En quelle année le premier Super Mario Bros. est-il sorti au Japon ?',
        'Which mathematician is associated with the theorem about right-angled triangles?': 'Quel mathématicien est associé au théorème sur les triangles rectangles ?',
        'How many bits are in a byte?': 'Combien de bits y a-t-il dans un octet ?',
        'Which ancient wonder was located in Alexandria?': 'Quelle merveille antique était située à Alexandrie ?',
        'How many symphonies did Beethoven compose?': 'Combien de symphonies Beethoven a-t-il composées ?',
        'What is the chemical symbol for Potassium?': 'Quel est le symbole chimique du potassium ?',
        'In which ocean is Madagascar located?': 'Dans quel océan Madagascar est-il situé ?',
        'Who wrote Don Quixote?': 'Qui a écrit Don Quichotte ?',
        'Which film won the first Academy Award for Best Picture in 1928?': 'Quel film a remporté le premier Oscar du meilleur film en 1928 ?',
        'Who wrote the novel 1984?': 'Qui a écrit le roman 1984 ?',
        'What is the tallest mountain in the world?': 'Quel est le plus haut sommet du monde ?',
        'What is the most abundant gas in Earth\'s atmosphere?': 'Quel est le gaz le plus abondant dans l\'atmosphère terrestre ?',
        'In what year was the original Nintendo Game Boy released?': 'En quelle année la Nintendo Game Boy originale a-t-elle été lancée ?',
        'Which Roman emperor ordered the construction of Hadrian\'s Wall?': 'Quel empereur romain a ordonné la construction du mur d\'Hadrien ?',
        'What is the pH of pure water?': 'Quel est le pH de l\'eau pure ?',
        'In music, what does forte mean?': 'En musique, que signifie forte ?',
        'What is the name of the deepest lake in the world?': 'Quel est le nom du plus profond lac du monde ?',
        'In which year did the Titanic sink?': 'En quelle année le Titanic a-t-il coulé ?',
        'What is the chemical symbol for iron?': 'Quel est le symbole chimique du fer ?',
        'How many gold medals did Usain Bolt win across the 2008, 2012 and 2016 Olympics?': 'Combien de médailles d\'or Usain Bolt a-t-il remportées aux Jeux olympiques de 2008, 2012 et 2016 ?',
        'What is the currency of Japan?': 'Quelle est la devise du Japon ?',
        'What is the process by which a caterpillar transforms into a butterfly?': 'Quel est le processus par lequel une chenille se transforme en papillon ?',
        'In what year did the United States declare independence?': 'En quelle année les États-Unis ont-ils déclaré leur indépendance ?',
        'Which country has the longest coastline in the world?': 'Quel pays possède la plus longue côte du monde ?',
        'In which Dickens novel does Ebenezer Scrooge appear?': 'Dans quel roman de Dickens apparaît Ebenezer Scrooge ?',
        'Which author created Sherlock Holmes?': 'Quel auteur a créé Sherlock Holmes ?',
        'Which treaty formally ended World War I?': 'Quel traité a mis fin officiellement à la Première Guerre mondiale ?',
        'What does DNA stand for?': 'Que signifie l\'acronyme ADN ?',
        'Which company developed The Legend of Zelda?': 'Quelle société a développé The Legend of Zelda ?',
        'What is the name of the galaxy in which we live?': 'Quel est le nom de la galaxie dans laquelle nous vivons ?',
        'Who was the first Holy Roman Emperor?': 'Qui a été le premier empereur du Saint-Empire romain ?',
        'Which instrument is Yo-Yo Ma famous for playing?': 'Quel instrument Yo-Yo Ma joue-t-il surtout ?',
        'What is the official name of the country commonly called Turkey?': 'Quel est le nom officiel du pays communément appelé Turquie ?',
        'Who developed the theory of general relativity?': 'Qui a développé la théorie de la relativité générale ?',
        'In which city is the United Nations headquarters?': 'Dans quelle ville se trouve le siège des Nations unies ?',
        'Which principle states you cannot simultaneously know both position and momentum of a particle?': 'Quel principe affirme qu\'on ne peut pas connaître simultanément la position et la quantité de mouvement d\'une particule ?',
        'Which river flows through the most countries in the world?': 'Quel fleuve traverse le plus de pays au monde ?',
        'Who wrote War and Peace?': 'Qui a écrit Guerre et Paix ?',
        'What is the chemical formula for ammonia?': 'Quelle est la formule chimique de l\'ammoniac ?',
        'In which year did Brazil win its first FIFA World Cup?': 'En quelle année le Brésil a-t-il remporté sa première Coupe du monde de la FIFA ?',
        'What is the name of the fictional kingdom in The Legend of Zelda?': 'Quel est le nom du royaume fictif de The Legend of Zelda ?',
        'What is the half-life of Carbon-14?': 'Quelle est la demi-vie du carbone 14 ?',
        'In what year was the Magna Carta signed?': 'En quelle année la Magna Carta a-t-elle été signée ?',
        'Among these, which element has the highest atomic number?': 'Parmi ceux-ci, quel élément a le plus grand numéro atomique ?',
        'In Homer\'s Iliad, which city did the Greeks besiege for ten years?': 'Dans l\'Iliade d\'Homère, quelle ville les Grecs ont-ils assiégée pendant dix ans ?',
        'What is the Planck constant approximately equal to?': 'À quoi la constante de Planck est-elle approximativement égale ?',
        'Which pharaoh is associated with the Great Pyramid at Giza?': 'Quel pharaon est associé à la grande pyramide de Gizeh ?',
        'Which composer wrote The Four Seasons?': 'Quel compositeur a écrit Les Quatre Saisons ?',
        'What is the name of the strait separating Europe from Africa?': 'Quel est le nom du détroit séparant l\'Europe de l\'Afrique ?',
        'Which physicist first proposed the existence of the Higgs boson?': 'Quel physicien a proposé pour la première fois l\'existence du boson de Higgs ?',
        'What was the name of the Allied D-Day operation in 1944?': 'Quel était le nom de l\'opération alliée du Débarquement en 1944 ?',
        'In Homer\'s Odyssey, what is the name of the one-eyed giant blinded by Odysseus?': 'Dans l\'Odyssée d\'Homère, quel est le nom du géant à un seul œil aveuglé par Ulysse ?',
        'What is the Chandrasekhar limit approximately?': 'À quoi la limite de Chandrasekhar est-elle approximativement égale ?',
        'Who wrote The Prince, the foundational text of political philosophy?': 'Qui a écrit Le Prince, texte fondamental de la philosophie politique ?',
        'What is the theoretical boundary around a black hole from which nothing can escape?': 'Quelle est la frontière théorique autour d\'un trou noir d\'où rien ne peut s\'échapper ?',
        'Which country contains the most of the Amazon rainforest?': 'Quel pays contient la majeure partie de la forêt amazonienne ?',
        'In which Shakespeare play does the villain Iago appear?': 'Dans quelle pièce de Shakespeare apparaît le vilain Iago ?',
        'What is the value of Pi to five decimal places?': 'Quelle est la valeur de pi à cinq décimales près ?',
        'What is the sum of all integers from 1 to 100?': 'Quelle est la somme de tous les entiers de 1 à 100 ?',
        'What is the name of the force carrier particle for the electromagnetic force?': 'Quel est le nom de la particule médiatrice de la force électromagnétique ?',
        'In a standard normal distribution, approximately what percentage of values lie within one standard deviation of the mean?': 'Dans une distribution normale standard, quel pourcentage approximatif de valeurs se situe à un écart-type de la moyenne ?',
        'What is the name of the process by which a solid turns directly into a gas without passing through the liquid phase?': 'Quel est le nom du processus par lequel un solide se transforme directement en gaz sans passer par la phase liquide ?',
        'Which battle in 1066 decided the fate of England?': 'Quelle bataille en 1066 a décidé du destin de l\'Angleterre ?',
        'What is the name of the theorem that states every integer greater than 1 is either prime or a product of primes?': 'Quel est le nom du théorème qui énonce que tout entier supérieur à 1 est soit premier soit un produit de nombres premiers ?',
        'What is the name of the quantum mechanical effect whereby a particle tunnels through a barrier it classically could not surmount?': 'Quel est le nom de l\'effet mécanique quantique par lequel une particule traverse une barrière qu\'elle ne pourrait normalement franchir ?',
        'Which conjecture states that every even integer greater than 2 is the sum of two primes?': 'Quelle conjecture affirme que tout entier pair supérieur à 2 est la somme de deux nombres premiers ?',
        'What is the Schwarzschild radius of a black hole with the mass of Earth?': 'Quel est le rayon de Schwarzschild d\'un trou noir ayant la masse de la Terre ?',
        'In Euler\'s identity, e^(iπ) + 1 = 0. What does \'e\' represent?': 'Dans l\'identité d\'Euler, e^(iπ) + 1 = 0. Que représente \"e\" ?',
        'What is the name of the hypothetical particle that travels faster than light?': 'Quel est le nom de la particule hypothétique qui voyage plus vite que la lumière ?',
        'In what year did the Library of Alexandria burn for the last time, effectively ending its existence?': 'En quelle année la bibliothèque d\'Alexandrie a-t-elle brûlé pour la dernière fois, mettant fin à son existence ?',
        'Which country won the first FIFA World Cup in 1930?': 'Quel pays a remporté la première Coupe du monde de la FIFA en 1930 ?',
        'Who won the Formula 1 World Championship in 1994?': 'Qui a remporté le championnat du monde de Formule 1 en 1994 ?',
        'Which driver won the most Formula 1 Grand Prix between 1950 and 1969?': 'Quel pilote a remporté le plus de Grands Prix de Formule 1 entre 1950 et 1969 ?',
        'Who won the Ligue 1 (French football championship) in the 2001-2002 season?': 'Qui a remporté la Ligue 1 (championnat de football français) lors de la saison 2001-2002 ?',
        'Which Formula 1 driver was World Champion in 1962?': 'Quel pilote de Formule 1 a été champion du monde en 1962 ?',
        'Which is the correct spelling of the large flowering shrub?': 'Quelle est l\'orthographe correcte du grand arbuste à fleurs ?',
        'Which is the correct spelling of the word meaning \'relating to the stomach\'?': 'Quelle est l\'orthographe correcte du mot signifiant \"relatif à l\'estomac\" ?',
        'Which is the correct spelling of the fear of spiders?': 'Quelle est l\'orthographe correcte du mot signifiant la peur des araignées ?',
        'Which is the correct spelling of the branch of medicine dealing with the nervous system?': 'Quelle est l\'orthographe correcte de la branche de la médecine qui traite du système nerveux ?',
        'Which is the correct spelling of the philosophical concept of the impossibility of certain knowledge?': 'Quelle est l\'orthographe correcte du concept philosophique de l\'impossibilité d\'une connaissance certaine ?',
    }
    translated = translations.get(text)
    if not translated:
        continue
    new_q = json.loads(json.dumps(en_q))
    new_q['question'] = translated
    # Keep same id but change prefix to fr_ for French pool.
    new_q['id'] = new_q['id'].replace('en_', 'fr_', 1)
    new_fr_questions.append(new_q)
    new_fr_ids.add(new_q['id'])

# Create English pool from the old English questions and add translated questions from the French pool when absent.
new_en_questions = []
new_en_ids = set()
for q in en_questions:
    q_copy = json.loads(json.dumps(q))
    q_copy['id'] = q_copy['id'].replace('en_', 'en_')
    new_en_questions.append(q_copy)
    new_en_ids.add(q_copy['id'])

# Add French questions that are not already covered and are safe to translate.
for q in fr_questions:
    # Skip if already present by id or if the underlying text is too different to translate simply.
    if q.get('id') in new_en_ids:
        continue
    # We'll include only questions that are simple factual questions and not overly idiomatic.
    text = q.get('question', '')
    if any(token in text for token in ['Combien', 'Quelle', 'Quel', 'De quelle', 'Sur quel', 'Dans quel', 'Qui', 'En quelle']) and 'signifie' not in text and 'orthographe' not in text:
        pass
    else:
        continue
    # Simple reverse mapping for a subset of the French questions already represented in the English pool.
    translations = {
        'Combien y a-t-il de jours dans une semaine ?': 'How many days are in a week?',
        'De quelle couleur est le ciel par beau temps ?': 'What color is the sky on a clear day?',
        'Quel animal produit du miel ?': 'What animal produces honey?',
        'Combien font 5 × 5 ?': 'What is 5 × 5?',
        'Combien y a-t-il de mois dans une année ?': 'How many months are in a year?',
        'Quelle est la couleur du soleil dans un dessin d\'enfant ?': 'What color is the sun in a child\'s drawing?',
        'Combien de pattes a une araignée ?': 'How many legs does a spider have?',
        'Quel est le résultat de 10 + 10 ?': 'What is the result of 10 + 10?',
        'Quelle est la capitale de la France ?': 'What is the capital of France?',
        'Combien y a-t-il de couleurs dans l\'arc-en-ciel ?': 'How many colors are in a rainbow?',
        'Combien de joueurs composent une équipe de football sur le terrain ?': 'How many players are on a football team on the pitch?',
        'Quel est le plus grand pays du monde par superficie ?': 'What is the largest country in the world by area?',
        'Sur quel continent se trouve le Brésil ?': 'On which continent is Brazil?',
        'Quelle est la capitale de l\'Espagne ?': 'What is the capital of Spain?',
        'Combien y a-t-il d\'heures dans une journée ?': 'How many hours are in a day?',
        'Quel animal est le symbole de la France ?': 'What animal is the symbol of France?',
        'Quelle est la formule chimique de l\'eau ?': 'What is the chemical formula for water?',
        'Quel sport se joue avec un volant ?': 'Which sport uses a shuttlecock?',
        'Sur quel continent se trouve l\'Égypte ?': 'On which continent is Egypt?',
        'Quel est l\'élément chimique de symbole Na ?': 'What is the chemical element with symbol Na?',
        'Quelle est la capitale du Royaume-Uni ?': 'What is the capital of the United Kingdom?',
        'Quel est le plus grand océan du monde ?': 'What is the largest ocean in the world?',
        'Quel pays possède le plus de lacs naturels au monde ?': 'Which country has the most natural lakes in the world?',
        'Quel est le plus petit pays du monde par superficie ?': 'What is the smallest country in the world by area?',
        'Quelle est la capitale de l\'Australie ?': 'What is the capital of Australia?',
        'Quel est le plus haut sommet du monde ?': 'What is the tallest mountain in the world?',
        'Quelle est la devise du Japon ?': 'What is the currency of Japan?',
    }
    translated = translations.get(text)
    if not translated:
        continue
    new_q = json.loads(json.dumps(q))
    new_q['question'] = translated
    new_q['id'] = new_q['id'].replace('fr_', 'en_', 1)
    new_en_questions.append(new_q)
    new_en_ids.add(new_q['id'])

# Normalize metadata.
for data, language in [(new_fr_questions, 'fr'), (new_en_questions, 'en')]:
    # remove duplicates by id preserves first occurrence.
    seen = set()
    deduped = []
    for q in data:
        qid = q.get('id')
        if qid in seen:
            continue
        seen.add(qid)
        deduped.append(q)
    data[:] = deduped

# Write files.
new_fr_meta = {
    '_meta': {
        'version': '3.0.0',
        'language': 'fr',
        'description': 'Pool de questions françaises pour Sub Ladder',
        'sources': ['Who Wants to Be a Millionaire? (UK/US)', 'Various TV quiz shows'],
        'level_fields': {
            'level_easy': 'Position dans une partie Facile (1-15, -1 = absente)',
            'level_normal': 'Position dans une partie Normale (1-15, -1 = absente)',
            'level_hard': 'Position dans une partie Difficile (1-15, -1 = absente)',
            'level_legendary': 'Position dans une partie Légendaire (1-15, -1 = absente)'
        },
        'themes': ['general','nature','geography','sport','science','mathematics','music','cinema','history','literature','videogames','spelling']
    },
    'questions': new_fr_questions
}
new_en_meta = {
    '_meta': {
        'version': '3.0.0',
        'language': 'en',
        'description': 'English question pool for Sub Ladder',
        'sources': ['Who Wants to Be a Millionaire? (UK/US)', 'Various TV quiz shows'],
        'level_fields': {
            'level_easy': 'Position in an Easy game (1-15, -1 = not used)',
            'level_normal': 'Position in a Normal game (1-15, -1 = not used)',
            'level_hard': 'Position in a Hard game (1-15, -1 = not used)',
            'level_legendary': 'Position in a Legendary game (1-15, -1 = not used)'
        },
        'themes': ['general','nature','geography','sport','science','mathematics','music','cinema','history','literature','videogames','spelling']
    },
    'questions': new_en_questions
}

with open(questions_dir / 'fr_questions.json', 'w', encoding='utf-8') as f:
    json.dump(new_fr_meta, f, ensure_ascii=False, indent=2)
    f.write('\n')
with open(questions_dir / 'en_questions.json', 'w', encoding='utf-8') as f:
    json.dump(new_en_meta, f, ensure_ascii=False, indent=2)
    f.write('\n')

print('wrote', len(new_fr_questions), 'fr questions and', len(new_en_questions), 'en questions')