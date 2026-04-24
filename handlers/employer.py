from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Vacancy, Application, Resume, User
from locales import LEXICON

router = Router()

class VacancyForm(StatesGroup):
    title = State()
    description = State()
    skills_required = State()
    type = State()
    microdistrict = State()
    schedule = State()
    salary = State()
    languages_required = State()

@router.message(lambda msg: msg.text in [LEXICON["ru"]["btn_create_vac"], LEXICON["kk"]["btn_create_vac"], LEXICON["en"]["btn_create_vac"]])
async def cmd_create_vacancy(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await message.answer(LEXICON[lang]["ask_v_title"])
    await state.set_state(VacancyForm.title)

@router.message(VacancyForm.title)
async def process_title(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(title=message.text)
    await message.answer(LEXICON[lang]["ask_v_desc"])
    await state.set_state(VacancyForm.description)

@router.message(VacancyForm.description)
async def process_description(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(description=message.text)
    await message.answer(LEXICON[lang]["ask_v_skills"])
    await state.set_state(VacancyForm.skills_required)

@router.message(VacancyForm.skills_required)
async def process_skills_required(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(skills_required=message.text)
    await message.answer(LEXICON[lang]["ask_v_type"])
    await state.set_state(VacancyForm.type)

@router.message(VacancyForm.type)
async def process_type(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(type=message.text)
    await message.answer(LEXICON[lang]["ask_v_district"])
    await state.set_state(VacancyForm.microdistrict)

@router.message(VacancyForm.microdistrict)
async def process_v_microdistrict(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(microdistrict=message.text)
    await message.answer(LEXICON[lang]["ask_v_schedule"])
    await state.set_state(VacancyForm.schedule)

@router.message(VacancyForm.schedule)
async def process_v_schedule(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(schedule=message.text)
    await message.answer(LEXICON[lang]["ask_v_salary"])
    await state.set_state(VacancyForm.salary)

@router.message(VacancyForm.salary)
async def process_v_salary(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    await state.update_data(salary=message.text)
    await message.answer(LEXICON[lang]["ask_v_lang"])
    await state.set_state(VacancyForm.languages_required)

@router.message(VacancyForm.languages_required)
async def process_v_languages(message: Message, session: AsyncSession, state: FSMContext):
    result_user = await session.execute(select(User).where(User.tg_id == message.from_user.id))
    lang = result_user.scalar_one().language
    
    data = await state.get_data()
    data['languages_required'] = message.text
    
    vacancy = Vacancy(
        employer_id=message.from_user.id,
        **data
    )
    session.add(vacancy)
    await session.commit()
    await state.clear()
    
    await message.answer(LEXICON[lang]["vac_saved"])

@router.message(lambda msg: msg.text in [LEXICON["ru"]["btn_my_vac"], LEXICON["kk"]["btn_my_vac"], LEXICON["en"]["btn_my_vac"]])
async def cmd_my_vacancies(message: Message, session: AsyncSession):
    result = await session.execute(select(Vacancy).where(Vacancy.employer_id == message.from_user.id))
    vacancies = result.scalars().all()
    
    if not vacancies:
        await message.answer("У вас пока нет активных вакансий / Белсенді бос орындарыңыз жоқ / No active vacancies.")
        return
        
    for v in vacancies:
        app_result = await session.execute(select(Application).where(Application.vacancy_id == v.id))
        apps = app_result.scalars().all()
        
        text = (f"📌 {v.title}\n"
                f"💰 {v.salary}\n"
                f"Откликов/Жауаптар/Apps: {len(apps)}")
        await message.answer(text)

@router.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def process_decision(callback: CallbackQuery, session: AsyncSession):
    action, app_id = callback.data.split("_")
    app_id = int(app_id)
    
    result = await session.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    
    if not app:
        await callback.answer("Not found", show_alert=True)
        return
        
    app.status = action
    await session.commit()
    
    res_result = await session.execute(select(Resume).where(Resume.id == app.resume_id))
    resume = res_result.scalar_one_or_none()
    
    vac_result = await session.execute(select(Vacancy).where(Vacancy.id == app.vacancy_id))
    vacancy = vac_result.scalar_one_or_none()
    
    if action == "accept":
        await callback.message.edit_text(callback.message.text + "\n\n✅ Принят / Қабылданды / Accepted!")
        try:
            await callback.bot.send_message(
                resume.user_id,
                f"🎉 Вас пригласили на вакансию / Сізді жұмысқа шақырды / You were invited: '{vacancy.title}'.\n"
                f"Контакт/Байланыс/Contact: @{callback.from_user.username}"
            )
        except:
            pass
    else:
        await callback.message.edit_text(callback.message.text + "\n\n❌ Отклонен / Бас тартылды / Rejected.")
        try:
            await callback.bot.send_message(
                resume.user_id,
                f"😔 Отказ по вакансии / Бос орын бойынша бас тарту / Rejection for: '{vacancy.title}'."
            )
        except:
            pass
    await callback.answer()
