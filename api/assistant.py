from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel
import logging
import env

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
api_client = OpenAI(api_key=env.OPENAI_PRIVATE_KEY)


# 열 번에 한 번 뛰어난 코드 리뷰를 하는 것보다  열번 모두 안정적인 코드 리뷰를 하는 게 중요
# 따라서 프롬프트 엔지니어링으로 코드의 다른 내용에 대해 정확하게 알지 못하는 경우, 그에 대한 언급은 피해주는 프롬프트 추가


class ReviewRequest(BaseModel):
    branch: str
    file_path: str
    code: str


class ReviewResponse(BaseModel):
    branch: str
    file_path: str
    code: str

class SampleCodeRequest(BaseModel):
    code: str
    comment: str

class SampleCodeResponse(BaseModel):
    sample_code: str

@router.get("/health-check")
def health_check():
    log.debug('health_check has been called')
    return 'ok'

@router.post("/sample", response_model=SampleCodeResponse)
def generate_sample_code(request: SampleCodeRequest) -> SampleCodeResponse:
    log.debug(f'generate_sample_code has been called with request: {request}')   
    result_code = get_sample_code(review=request, assistant_id=env.SAMPLECODE_GENERATOR_ID)

    result = SampleCodeResponse(sample_code=result_code)

    # swagger를 통한 테스트 편의상 일단 return 하도록 놔둠.
    # 추후에 ORM을 이용해서 DB를 저장할 지 고려중
    return result


# TODO 비동기로 최적화 하기
@router.post("/pulls", response_model=ReviewResponse)
def generate_pr_code_review(review: ReviewRequest) -> ReviewResponse:
    log.debug(f'generate_pr_code_review has been called with request: {review}')
    result_code = get_review_code(review=review, assistant_id=env.PR_STATIC_ANALYSIS_ID)

    result = ReviewResponse(branch=review.branch,
                                             file_path=review.file_path,
                                             code=result_code)

    return result


def get_review_code(review: ReviewRequest, assistant_id: str) -> str:
    log.debug(f'get_review_code has been called with request: {review}')
    try:
        # 매 파일마다 새로운 Thread를 생성함.
        thread = api_client.beta.threads.create()
        # 메세지 생성
        api_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=review.code
        )
        # 실행
        run = api_client.beta.threads.runs.create_and_poll(
            assistant_id=assistant_id,
            thread_id=thread.id
        )

        while run.status != "completed":
            ...

        messages = api_client.beta.threads.messages.list(
            thread_id=thread.id,
        )

        return messages.data[0].content[0].text.value

    except Exception as e:
        log.warning(f'Error procesing review for {review.file_path}, e: {e}')
        raise HTTPException(status_code=500, detail=f"Error processing review for {review.file_path}: {e}")


def get_sample_code(review: SampleCodeRequest, assistant_id: str) -> str:
    log.debug(f'get_sample_code has been called with request: {review}')
    try:

        thread = api_client.beta.threads.create()

        api_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"""
            <Comment>
            {review.comment}
            </Comment>
            <Code>
            ```
            {review.code}
            ```
            </Code>
            """)

        # 실행
        run = api_client.beta.threads.runs.create_and_poll(
            assistant_id=assistant_id,
            thread_id=thread.id
        )

        while run.status != "completed":
            ...

        messages = api_client.beta.threads.messages.list(
            thread_id=thread.id,
        )

        return messages.data[0].content[0].text.value

    except Exception as e:
        log.warning(f'Error generating sample code: {e}')
        raise HTTPException(status_code=500, detail=f"Error Generating Sample Code: {e}")
