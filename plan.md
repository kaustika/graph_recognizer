
## План решения

Потенциально на данный момент мы имеем __два основных пути нахождения ограничивающих прямоугольников (баундбоксов)__, по которым впоследствии будет строится детерминированным образом список смежности распознанного графа.

___Нахождение баундбоксов___:
1.  __С использованием нейронных сетей__
	 Обучить нейронную сеть искать баундбоксы для ребер двух типов и вершин графа. Может быть дообучена сеть, уже умеющая выделять оъекты, например Facebook Detectron 2, для которой есть [инструкции для дообучения по custom-данным](https://colab.research.google.com/drive/16jcaJoc6bCFAQ96jDe2HwtXj7BMD_-m5#scrollTo=b2bjrfb2LDeo).
    
2.  __С использованием не ML-алгоритмов распознавания__
     Сегментировать изображение не-ML методами поиска границ и примитивов - ищем прямые отрезки и окружности. Нам потребуется подход с распознаванием границ, скажем, методом Canny (параметры и пороги подберем, перебирая с каким-то небольшим шагом и смотря глазами на границы) и выделением на них прямых преобразованием Хафа. Для детекции окружностей должен хорошо сработать поиск блобов.

___Классификация баундбоксов___:
- В случае использования нейронных сетей для классификации может быть использована либо та же нейронная сеть, что использовалась для их выделения, либо построена новая простая, служащая целям только классификации. 
- В случае же использования не ML-алгоритмов дифференцировка между классами баундбоксов "ребро" и "вершина" происходит уже на этапе поиска соответсвующих баундбоксов.

В рамках обоих путей решения может быть использован или не использован в качестве вспомогательного для дифференцировки цветовой признак ребер, вершин и меток.

___Распознавание текста меток:___
- Для обоих путей соответствующие метки вершин будут локализованы в найденных окружностях, после чего для распознавания (а, может, и детекции) текста будут использованы средства библиотеки OpenCV OCR. Шрифт Tahoma в поставновке может быть и сменен, хоть и является, согласно форумам, хорошо [раcпознаваемым](https://www.capturebites.com/2016/03/15/ocr-font/).

___Составление списка смежности по распознанной информации:___
- Так как после распознавания баундбоксов для ребер и вершин нам будет известно их взаимное расположение (знаем координаты вершин баундбоксов -> их наконы друг относительно друга, их близость), можем построить детерминированный алгоритм, определяющий вершины и ребро, образующие связь. 
- Каждое обнаруженное сетью ребро должно иметь вершины, которые оно соединяет. Заметим, что связанные вершины лежат на одной линии, на большей оси симметрии баундбокса ребра. Для каждого ребра находим баундбоксы вершин, пересекаемые большей осью симметрии баундбокса ребра. Из найденных лежащих на одной прямой считаем состоящими в связи те две вершины, для которых расстояние между баундбоксом ребра и ними минимально.
- Метка же изначально однозначно сопоставляется вершине, так как текст распознается внутри баундбокса вершины.


Я оставляю за собой на данном этапе возможность выбора между двумя возможными путями поиска баундбоксов. Нужно обратить внимание на то, что использование нейронных сетей сопряжено с необходимостью сгенерировать большой объем изображений планарных графов с размеченными баундбоксами, наших данных для обучения:

___Генерация данных___:

Сейчас генерацию я вижу так:
1. [Overpass API Python wrapper](https://github.com/mvexel/overpass-api-python-wrapper) для запросов к данным OSM.
2. Запрашиваться будут дороги городов России:
	- крупные города такие, как Москва и Санкт-Петербург;
	- чтобы не получать гигантские сложные графы, запрос будет включать в себя фильтр по некоторой окрестности ''' around lat="40.743560" lon="-73.992341" radius="50"'''.
3. Результат запроса будет сохраняться в json;
4. По json будет построен список смежности, в котором:
	- выбор типа ребра и значения метки будет случайным;
	- уникальные двусимвольные метки, соответствующие описанию в постановке, будут генерироваться по количеству вершин пришедшего из OSM графа.
	Список смежности будет опционально сохранен в бинарном виде для упрощения работы checker'а.
5. По списку смежности утилитой graphviz будет отрисован граф и сохранен в формате .png. При отрисовке будут учитываться координаты вершин графа, пришедшие из OSM, что позволит удовлетворить требованию планарности.
6. Для обучения на таких данных нейросети для поиска баундбоквов нам понадобятся данные с координатами вершин этих прямоугольников. Для каждого типа объекта, который мы будем учить сеть ограничивать и идентифицировать, мы сохраним координаты прямоугольника и метку - вершина/ребро типа 1/ребро типа 2. Информация о координатах прямоугольников может быть получена при отрисовке, исходя из характерной величины в пикселях окружностей вершин и их позиций, которые мы сами передали в graphviz.
7. Для хорошего дообучения сети Facebook Detectron 2 хотелось бы иметь не менее 5т размеченных изображений.

Нужно понимать, что генерация из OSM-открытых данных может стать сама по себе объемной задачей и, даже понимая всю важность хорошего сбора данных для решения каждой задачи в реальном мире, в данном курсе для меня важно посвятить больше времени реализации алгоритма.