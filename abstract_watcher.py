import asyncio
import abc
from typing import Coroutine, Any

"""
Описание задачи:
    Необходимо реализовать планировщик, позволяющий запускать и отслеживать фоновые корутины.
    Планировщик должен обеспечивать:
        - возможность планирования новой задачи
        - отслеживание состояния завершенных задач (сохранение результатов их выполнения)
        - отмену незавершенных задач перед остановкой работы планировщика
        
    Ниже представлен интерфейс, которому должна соответствовать ваша реализация.
    
    Обратите внимание, что перед завершением работы планировщика, все запущенные им корутины должны быть
    корректным образом завершены.
    
    В папке tests вы найдете тесты, с помощью которых мы будем проверять работоспособность вашей реализации
    
"""


class AbstractRegistrator(abc.ABC):
    """
    Сохраняет результаты работы завершенных задач.
    В тестах мы передадим в ваш Watcher нашу реализацию Registrator и проверим корректность сохранения результатов.
    """

    @abc.abstractmethod
    def register_value(self, value: Any) -> None:
        # Store values returned from done task
        ...

    @abc.abstractmethod
    def register_error(self, error: BaseException) -> None:
        # Store exceptions returned from done task
        ...


class AbstractWatcher(abc.ABC):
    """
    Абстрактный интерфейс, которому должна соответсововать ваша реализация Watcher.
    При тестировании мы расчитываем на то, что этот интерфейс будет соблюден.
    """

    def __init__(self, registrator: AbstractRegistrator):
        self.registrator = registrator  # we expect to find registrator here

    @abc.abstractmethod
    async def start(self) -> None:
        # Good idea is to implement here all necessary for start watcher :)
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        # Method will be called on the end of the Watcher's work
        ...

    @abc.abstractmethod
    def start_and_watch(self, coro: Coroutine) -> None:
        # Start new task and put to watching
        ...


class StudentWatcher(AbstractWatcher):
    def __init__(self, registrator: AbstractRegistrator):
        super().__init__(registrator)
        # Your code goes here

        # set with planned tasks
        self.planned_tasks = set()
            
    async def start(self) -> None:
        self.watcher = asyncio.create_task(self.watching_coro())

    async def stop(self) -> None:
        num_registered_tasks = -1
        # register executed tasks if exist
        if len(self.planned_tasks): 
            num_registered_tasks = await self.register_results()

        # cancel all other tasks
        if len(self.planned_tasks):
            for task in self.planned_tasks:
                task.cancel()
            await asyncio.wait(self.planned_tasks, return_when=asyncio.ALL_COMPLETED)
        
        # cancel watcher-coro
        self.watcher.cancel()
        await asyncio.wait([self.watcher])

    def start_and_watch(self, coro: Coroutine) -> None:
        # create and plan new task
        task = asyncio.create_task(coro)
        self.planned_tasks.add(task)

    async def watching_coro(self) -> None:
        while True:
            # sleep 0.1s if no planned tasks
            if len(self.planned_tasks) == 0:
                await asyncio.sleep(0.1)
                continue

            # register results of all executed tasks
            await self.register_results()

    async def register_results(self) -> None:
        # waiting some of planned tasks with timeout
        done, pending = await asyncio.wait(self.planned_tasks, timeout=0.1)

        # register results and errors of executed tasks
        for task in done:
            exc = task.exception()
            if exc:
                self.registrator.register_error(exc)
            else:
                self.registrator.register_value(task.result())
        
        # update set of planned tasks
        self.planned_tasks = pending

        return len(done)
