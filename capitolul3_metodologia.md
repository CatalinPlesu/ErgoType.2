# 3. METODOLOGIA CERCETĂRII

## 3.1 ARHITECTURA GENERALĂ A SISTEMULUI

Această cercetare abordează problema optimizării layout-urilor de tastatură prin intermediul algoritmilor genetici, oferind o soluție automată și obiectivă pentru proiectarea unui layout ergonomic. Arhitectura sistemului este compusă din patru componente principale care gestionează modelarea atât a aspectelor fizice (poziția tastelor în spațiul 2D) cât și logice (maparea caracterelor la poziții), implementează funcția obiectiv care cuantifică eficiența unui layout prin metrici ergonomice, aplică operatori evolutivi pentru explorarea spațiului soluțiilor și compară layout-urile generate cu standardele existente.

Sistemul procesează un corpus extins de text pentru a determina frecvențele de utilizare ale caracterelor și combinațiilor acestora, asigurând o optimizare bazată pe date reale de utilizare. Această abordare empirică contrastează cu metodele tradiționale care se bazează pe intuiție sau pe analiza limitată a unor subseturi mici de text.

## 3.2 REPREZENTAREA LAYOUT-URILOR

Modelul fizic reprezintă tastatura ca o grilă 2D în care fiecare tastă are coordonate spațiale precise. Această reprezentare este esențială pentru calculul distanțelor reale pe care trebuie să le parcurgă degetele utilizatorului. Fiecare tastă este definită prin coordonatele sale $(x, y)$ în spațiul tastaturii. Distanța euclidiană dintre două taste $i$ și $j$ este calculată ca:

$$d_{ij} = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2} \quad (3.1)$$

Această abordare permite suportul pentru diverse forme fizice de tastaturi cum ar fi ANSI standard, ISO european, tastaturi ergonomice split sau columnar, precum și layout-uri specifice laptopurilor ThinkPad. Modelul logic operează la nivelul permutărilor de caractere. Un layout este reprezentat ca o bijecție între mulțimea caracterelor și mulțimea pozițiilor fizice. Genotipul reprezintă cromozomul ca o secvență ordonată de caractere, în timp ce fenotipul este layout-ul complet, rezultatul mapării genotipului pe pozițiile fizice ale tastaturii. Această separare permite aplicarea operatorilor genetici în spațiul permutărilor, unde sunt mai naturali și mai eficienți.

O inovație importantă a acestei cercetări este utilizarea unui model stateful pentru trackingul pozițiilor degetelor. Spre deosebire de abordările tradiționale care consideră fiecare apăsare independentă, acest model ține evidența poziției curente a fiecărui deget. Starea unui deget este definită ca un tuplu $(p, t)$ unde $p$ este poziția fizică a degetului (indexul tastei) și $t$ este timestampul ultimei utilizări. Pentru a evita biasul introdus de texte foarte lungi sau repetitive, pozițiile degetelor sunt resetate la poziția de "acasă" (home row) la fiecare 255 de caractere procesate. Această resetare imită comportamentul natural al utilizatorilor care își repositionează frecvent mâinile.

## 3.3 FUNCȚIA OBIECTIV (FITNESS)

Funcția de fitness combină două metrici principale într-o sumă ponderată:

$$F = w_1 \cdot \text{norm}(D_{total}) + w_2 \cdot \text{norm}(T_{total}) \quad (3.2)$$

unde $w_1 = w_2 = 0.5$, asigurând o importanță egală între aspectele spațiale și temporale ale ergonomiei. Distanța totală este calculată ca suma distanțelor parcurse de fiecare deget în parte, ținând cont de poziția anterioară a acestuia:

$$D_{total} = \sum_{k=1}^{n} d_{i_k j_k} \quad (3.3)$$

unde $d_{i_k j_k}$ este distanța dintre poziția anterioară $i_k$ și poziția curentă $j_k$ a degetului $k$, iar $n$ este numărul total de apăsări. Utilizarea modelului stateful permite calcularea corectă a distanțelor reale parcurse, inclusiv pentru secvențe repetitive sau patternuri complexe de typing.

Pentru calculul timpului necesar pentru apăsarea unei taste, am implementat Legea lui Fitts, care este considerată standardul de aur în evaluarea performanței task-urilor de pointing. Timpul total este calculat ca suma aplicării legii lui Fitts pentru fiecare mișcare:

$$T_{total} = \sum_{k=1}^{n} \left[ a + b \cdot \log_2\left(\frac{d_{i_k j_k}}{W} + 1\right) \right] \quad (3.4)$$

unde $a$ este timpul de overhead constant (independent de distanță), $b$ este factorul de dificultate al task-ului, $d_{i_k j_k}$ este distanța de mișcare pentru apăsarea $k$, iar $W$ este lățimea țintei (în acest caz, dimensiunea tastei). Această formulă surprinde aspectul temporal al ergonomiei, ținând cont că mișcările mai lungi și mai precise necesită mai mult timp și efort.

O caracteristică importantă a modelului este separarea clară între mișcările degetelor (care pot fi paralele) și apăsările tastelor (care sunt seriale). Degetele pot călători simultan către pozițiile lor țintă, ceea ce este realist deoarece în typing-ul proficient, degetele se mișcă deseori în avans, pregătindu-se pentru următoarele apăsări. Doar un singur deget poate apăsa o tastă la un moment dat, ceea ce introduce o constrângere temporală naturală. Combinațiile de caractere consecutive care necesită utilizarea aceluiași deget sunt penalizate implicit prin sincronizarea necesară. Dacă două caractere consecutive trebuie apăsate de același deget, acel deget trebuie să execute două mișcări distincte, ceea ce crește timpul total. Pentru a modela timpul minim necesar pentru overlap-ul mișcărilor, am introdus o constantă de sincronizare ε care asigură că mișcările nu pot fi complet simultane.

Pentru a combina cele două metrici (distanță și timp) într-un singur scor de fitness, am aplicat o normalizare min-max pe fiecare metrică:

$$\text{norm}(x) = \frac{x - x_{min}}{x_{max} - x_{min}} \quad (3.5)$$

Valorile normalizate sunt apoi combinate liniar cu ponderile specificate. Acestă abordare asigură că ambele metrici contribuie echitabil la evaluarea finală, indiferent de unitățile lor de măsură diferite.

## 3.4 CORPUSUL DE TEXT ȘI PREPROCESARE

Corpusul utilizat pentru optimizare este diversificat și cuprinde multiple tipuri de texte. Textele în limba română includ literatură clasică și contemporană, articole științifice și tehnice, conținut de pe forumuri și platforme online, precum și texte de programare în context românesc. Textele în limba engleză includ opere literare clasice (Shakespeare, Dickens, Austen), texte științifice și tehnice, documentație software și standarde, precum și conținut web diversificat. Codul sursă este reprezentat prin programe în Python, JavaScript, C++, Java, algoritmi și structuri de date, framework-uri și biblioteci populare, precum și exemple de programare didactică.

Procesarea textului implică mai mulți pași pentru a asigura calitatea și consistența datelor. Curățarea textului elimină caracterele non-printabile, spațiile multiple și formaturile inconsistente. Normalizarea diacriticelor convertește literele cu diacritice în echivalentele lor fără diacritice pentru a reduce complexitatea. Filtrarea caracterelor păstrează doar caracterele relevante pentru typing (litere, cifre, semne de punctuație comune). Analiza frecvențelor calculează frecvențele pentru unigrame, bigrame și trigrame. Această abordare asigură că optimizarea se bazează pe patternuri reale de utilizare, reflectând atât scrierea naturală cât și activitățile specifice de programare.

## 3.5 ALGORITMUL GENETIC IMPLEMENTAT

Fiecare layout este reprezentat ca un cromozom care este o permutare a mulțimii de caractere esențiale. Lungimea cromozomului este determinată de acoperirea dorită - în implementarea noastră, am ales să lucrăm cu aproximativ 30-50 de caractere care acoperă peste 95% din utilizarea tipică. Reprezentarea ca permutare asigură că fiecare caracter apare exact o dată în layout, satisfăcând constrângerea fundamentală a unei tastaturi funcționale.

Populația inițială este generată prin o abordare hibridă. Include layout-urile cunoscute (QWERTY, Dvorak, Colemak, Workman, Norman) pentru a asigura un punct de plecare de calitate, generează o parte din populație prin amestecarea complet aleatorie a caracterelor și creează descendenți ai layout-urilor clasice prin mutații mici, combinând cunoașterea existentă cu explorarea spațiului. Dimensiunea populației este setată empiric la un nivel care asigură diversitate suficientă fără a compromite eficiența computațională.

Încrucișarea este implementată ca uniform crossover, care creează mai mulți descendenți (4 descendenți per pereche de părinți) prin amestecarea aleatorie a genelor părinților cu o tendință de a păstra mai multe caractere de la părintele cu fitness mai bun. Operatorul de mutație este Swap Mutation, care schimbă între ele pozițiile a două caractere alese aleatoriu. Mutația este adaptativă - rata de bază este de 0.05, dar crește în perioadele de stagnare pentru a promova diversitatea. Numărul de mutații aplicate este și el adaptativ, variind de la 1 la 5 în funcție de numărul de generații consecutive de stagnare.

Selecția părinților utilizează selecția prin turnir cu dimensiunea 3, care oferă un bun echilibru între presiunea selectivă și diversitatea populației. Supraviețuirea generației este implementată ca elitism pur: întreaga generație următoare este formată din cei mai buni indivizi ai generației curente, fără a păstra indivizi din generația anterioară.

Algoritmul se oprește atunci când una dintre următoarele condiții este îndeplinită: număr maxim de generații $G_{max} = 100$ (configurabil din fișierul de parametri) sau stagnare evolutivă (dacă populația nu se schimbă timp de 15 generații consecutive, valoare și ea configurabilă). Parametrii algoritmului genetic (dimensiunea populației, rata de mutație, numărul maxim de generații, limita de stagnare) pot fi controlați din fișierul de configurație `src/config/config.py`.

## 3.6 VALIDARE ȘI TESTARE

Layout-urile generate sunt comparate sistematic cu standardele actuale. Layout-urile clasice testate includ QWERTY (standardul actual, utilizat ca baseline), Dvorak (primul layout ergonomic major), Colemak (layout modern, echilibrat), Workman (layout axat pe ergonomie fizică), Norman (layout care încearcă să păstreze familiaritatea QWERTY), Asset și alte layout-uri existente. Compararea se face pe ambele metrici (distanță și timp) și pe scorul agregat de fitness.

Pentru a evalua robustețea layout-urilor logice, acestea sunt testate pe diverse forme fizice de tastaturi: ANSI standard (forma cea mai comună), ISO standard (cu dimensiuni ușor diferite), tastatură ThinkPad (cu layout specific laptopurilor) și tastatură ergonomică split (pentru evaluarea performanței pe forme neconvenționale). Această evaluare multiplă asigură că layout-urile generate sunt adaptabile la diverse configurații hardware, crescând valoarea lor practică.

Validarea actuală este realizată prin compararea cu layout-urile existente pe întregul corpus de text procesat, fără împărțirea în subseturi de antrenament și testare. Această abordare oferă o evaluare completă a performanței layout-urilor pe întreaga colecție de texte disponibile. Sistemul folosește un cache sofisticat pentru a evita recalculările costisitoare ale fitness-ului pentru layout-urile deja evaluate.